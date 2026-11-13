package wcp

import (
	"encoding/json"
	"net/http"
)

// NewRouter returns an http.Handler that exposes any World as a
// WCP/0.1 entity. If the world implements SubRegistrar, the router
// also exposes GET /sub_entities.
func NewRouter(world World) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("/manifest", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			writeError(w, 405, "method not allowed")
			return
		}
		writeJSON(w, 200, world.Manifest())
	})

	mux.HandleFunc("/log", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			writeError(w, 405, "method not allowed")
			return
		}
		since := r.URL.Query().Get("since")
		writeJSON(w, 200, map[string]any{"entries": world.LogSince(since)})
	})

	mux.HandleFunc("/petition", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			writeError(w, 405, "method not allowed")
			return
		}
		var req PetitionRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, 400, "invalid petition: "+err.Error())
			return
		}
		writeJSON(w, 200, world.Petition(req))
	})

	mux.HandleFunc("/act", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			writeError(w, 405, "method not allowed")
			return
		}
		var req ActRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeError(w, 400, "invalid act: "+err.Error())
			return
		}
		writeJSON(w, 200, world.Act(req))
	})

	if sr, ok := world.(SubRegistrar); ok {
		mux.HandleFunc("/sub_entities", func(w http.ResponseWriter, r *http.Request) {
			if r.Method != "GET" {
				writeError(w, 405, "method not allowed")
				return
			}
			writeJSON(w, 200, map[string]any{"entities": sr.ListSubEntities()})
		})
	}

	return mux
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	b, err := json.Marshal(body)
	if err != nil {
		http.Error(w, `{"error":"marshal"}`, 500)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	w.Write(b)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"error": msg})
}
