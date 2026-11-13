package wcp

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"
)

// Registry is a WCP/0.1 multiverse registry. It lists entities,
// verifies them against the canonical conformance CLI, and never
// converges (a catalog is a living thing).
type Registry struct {
	manifest Manifest
	mu       sync.RWMutex
	log      []LogEntry
	admitted map[string]string // token → timestamp
	entities map[string]Manifest
}

// NewRegistry constructs a multiverse registry.
func NewRegistry(entityID, name string) *Registry {
	sub := "multiverse://" + entityID + "/worlds"
	return &Registry{
		manifest: Manifest{
			EntityID:            entityID,
			Name:                name,
			ProtocolVersion:     "WCP/0.1",
			LawURL:              "multiverse://" + entityID + "/law",
			ActEndpoint:         "multiverse://" + entityID + "/act",
			LogEndpoint:         "multiverse://" + entityID + "/log",
			SubRegistryEndpoint: &sub,
		},
		admitted: map[string]string{},
		entities: map[string]Manifest{},
	}
}

func (r *Registry) Manifest() Manifest {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.manifest
}

func (r *Registry) Petition(req PetitionRequest) PetitionResponse {
	r.mu.Lock()
	defer r.mu.Unlock()
	ts := nowISO()
	if _, ok := r.admitted[req.PetitionerToken]; ok {
		r.append(LogEntry{Timestamp: ts, Kind: "petition_refused",
			ActorToken: &req.PetitionerToken,
			Data:       map[string]any{"reason": "Already admitted"}})
		return PetitionResponse{Kind: "refusal", Reason: "Already admitted"}
	}
	r.admitted[req.PetitionerToken] = ts
	r.append(LogEntry{Timestamp: ts, Kind: "admission",
		ActorToken: &req.PetitionerToken,
		Data:       map[string]any{"name": req.PetitionerName}})
	return PetitionResponse{Kind: "admission", EntityID: r.manifest.EntityID, Timestamp: ts}
}

func (r *Registry) Act(req ActRequest) ActResponse {
	ts := nowISO()
	r.mu.RLock()
	_, isAdmitted := r.admitted[req.ActorToken]
	r.mu.RUnlock()
	if !isAdmitted {
		r.mu.Lock()
		r.append(LogEntry{Timestamp: ts, Kind: "act_refused",
			ActorToken: &req.ActorToken,
			Data:       map[string]any{"reason": "Actor is not admitted"}})
		r.mu.Unlock()
		return ActResponse{Kind: "refusal", Reason: "Actor is not admitted"}
	}

	switch req.Type {
	case "multiverse.admit":
		return r.handleAdmit(ts, req)
	case "multiverse.remove":
		return r.handleRemove(ts, req)
	}
	r.mu.Lock()
	r.append(LogEntry{Timestamp: ts, Kind: "act_refused",
		ActorToken: &req.ActorToken,
		Data:       map[string]any{"reason": "Unknown act type: " + req.Type}})
	r.mu.Unlock()
	return ActResponse{Kind: "refusal", Reason: "Unknown act type: " + req.Type}
}

func (r *Registry) handleAdmit(ts string, req ActRequest) ActResponse {
	urlStr, _ := req.Payload["entity_url"].(string)
	if urlStr == "" {
		return ActResponse{Kind: "refusal", Reason: "No entity_url in payload"}
	}

	m, err := fetchManifest(urlStr)
	if err != nil {
		return ActResponse{Kind: "refusal",
			Reason: fmt.Sprintf("Could not fetch manifest: %v", err)}
	}

	r.mu.RLock()
	_, exists := r.entities[m.EntityID]
	r.mu.RUnlock()
	if exists {
		return ActResponse{Kind: "refusal",
			Reason: "Entity " + m.EntityID + " already listed"}
	}

	passed, failures, _ := RunConformance(urlStr)
	if !passed {
		r.mu.Lock()
		r.append(LogEntry{Timestamp: ts, Kind: "entity_admit_refused",
			ActorToken: &req.ActorToken,
			Data: map[string]any{
				"entity_id":   m.EntityID,
				"url":         urlStr,
				"failures":    failures,
			}})
		r.mu.Unlock()
		return ActResponse{Kind: "refusal",
			Reason: "Entity " + m.EntityID + " fails conformance"}
	}

	r.mu.Lock()
	r.entities[m.EntityID] = m
	r.append(LogEntry{Timestamp: ts, Kind: "entity_admitted",
		ActorToken: &req.ActorToken,
		Data: map[string]any{
			"entity_id": m.EntityID,
			"url":       urlStr,
			"manifest":  m,
		}})
	r.mu.Unlock()
	return ActResponse{Kind: "ack", EntityID: r.manifest.EntityID, Timestamp: ts}
}

func (r *Registry) handleRemove(ts string, req ActRequest) ActResponse {
	id, _ := req.Payload["entity_id"].(string)
	if id == "" {
		return ActResponse{Kind: "refusal", Reason: "No entity_id in payload"}
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.entities[id]; !ok {
		return ActResponse{Kind: "refusal",
			Reason: "Entity " + id + " not in registry"}
	}
	delete(r.entities, id)
	r.append(LogEntry{Timestamp: ts, Kind: "entity_removed",
		ActorToken: &req.ActorToken,
		Data:       map[string]any{"entity_id": id}})
	return ActResponse{Kind: "ack", EntityID: r.manifest.EntityID, Timestamp: ts}
}

func (r *Registry) LogSince(since string) []LogEntry {
	r.mu.RLock()
	defer r.mu.RUnlock()
	if since == "" {
		out := make([]LogEntry, len(r.log))
		copy(out, r.log)
		return out
	}
	var out []LogEntry
	for _, e := range r.log {
		if e.Timestamp > since {
			out = append(out, e)
		}
	}
	return out
}

func (r *Registry) ListSubEntities() []Manifest {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make([]Manifest, 0, len(r.entities))
	for _, m := range r.entities {
		out = append(out, m)
	}
	return out
}

func (r *Registry) append(e LogEntry) {
	r.log = append(r.log, e)
}

func fetchManifest(baseURL string) (Manifest, error) {
	var m Manifest
	c := NewClient(baseURL)
	var err error
	m, err = c.GetManifest()
	if err != nil {
		return m, err
	}
	// Validate the required protocol version
	if m.ProtocolVersion != "WCP/0.1" {
		return m, fmt.Errorf("unsupported protocol_version: %s", m.ProtocolVersion)
	}
	return m, nil
}

func nowISO() string {
	return time.Now().UTC().Format(time.RFC3339Nano)
}

func randomToken() string {
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

var _ = json.Marshal // silence unused in some build configs
var _ = strings.TrimSpace
var _ = http.DefaultClient
var _ = randomToken
