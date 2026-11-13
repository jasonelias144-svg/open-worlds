package main

import (
	"log"
	"net/http"
	"os"

	"wcp/wcp"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "9002"
	}
	entityID := os.Getenv("ENTITY_ID")
	if entityID == "" {
		entityID = "multiverse:go"
	}
	name := os.Getenv("NAME")
	if name == "" {
		name = "Go Multiverse"
	}

	reg := wcp.NewRegistry(entityID, name)
	router := wcp.NewRouter(reg)

	log.Printf("Go Multiverse at http://localhost:%s", port)
	log.Printf("  manifest:     http://localhost:%s/manifest", port)
	log.Printf("  sub-entities: http://localhost:%s/sub_entities", port)
	log.Fatal(http.ListenAndServe(":"+port, router))
}
