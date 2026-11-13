// WCP/0.1 types. JSON tags match the spec exactly.
package wcp

// Manifest is returned by GET /manifest (§4.1).
type Manifest struct {
	EntityID           string  `json:"entity_id"`
	Name               string  `json:"name"`
	ProtocolVersion    string  `json:"protocol_version"`
	LawURL             string  `json:"law_url"`
	ActEndpoint        string  `json:"act_endpoint"`
	LogEndpoint        string  `json:"log_endpoint"`
	SubRegistryEndpoint *string `json:"sub_registry_endpoint"`
}

// PetitionRequest is the body of POST /petition (§4.2).
type PetitionRequest struct {
	PetitionerToken    string      `json:"petitioner_token"`
	PetitionerName     string      `json:"petitioner_name"`
	PassportAdmissions [][2]string `json:"passport_admissions"`
	Message            string      `json:"message"`
	Target             *string     `json:"target,omitempty"`
}

// ActRequest is the body of POST /act (§4.3).
type ActRequest struct {
	ActorToken string         `json:"actor_token"`
	Type       string         `json:"type"`
	Payload    map[string]any `json:"payload"`
}

// LogEntry is one entry in the log (§4.4).
type LogEntry struct {
	Timestamp  string         `json:"timestamp"`
	Kind       string         `json:"kind"`
	ActorToken *string        `json:"actor_token"`
	Data       map[string]any `json:"data"`
}

// PetitionResponse is the discriminated union of Admission, Refusal,
// and Route (§5.2–5.4). Callers branch on Kind.
type PetitionResponse struct {
	Kind           string    `json:"kind"`
	EntityID       string    `json:"entity_id,omitempty"`       // admission
	Timestamp      string    `json:"timestamp,omitempty"`        // admission
	Reason         string    `json:"reason,omitempty"`           // refusal / route
	TargetManifest *Manifest `json:"target_manifest,omitempty"`  // route
}

func (r PetitionResponse) IsAdmission() bool { return r.Kind == "admission" }
func (r PetitionResponse) IsRefusal() bool   { return r.Kind == "refusal" }
func (r PetitionResponse) IsRoute() bool     { return r.Kind == "route" }

// ActResponse is the discriminated union of Ack and Refusal (§5.3, 5.5).
type ActResponse struct {
	Kind      string `json:"kind"`
	EntityID  string `json:"entity_id,omitempty"` // ack
	Timestamp string `json:"timestamp,omitempty"` // ack
	Reason    string `json:"reason,omitempty"`    // refusal
}

func (r ActResponse) IsAck() bool     { return r.Kind == "ack" }
func (r ActResponse) IsRefusal() bool { return r.Kind == "refusal" }

// World is what any WCP/0.1 entity must implement on the server side.
type World interface {
	Manifest() Manifest
	Petition(req PetitionRequest) PetitionResponse
	Act(req ActRequest) ActResponse
	LogSince(since string) []LogEntry
}

// SubRegistrar is an optional interface a world implements if it has
// a sub-registry. The Router exposes /sub_entities iff the world
// implements this interface.
type SubRegistrar interface {
	ListSubEntities() []Manifest
}
