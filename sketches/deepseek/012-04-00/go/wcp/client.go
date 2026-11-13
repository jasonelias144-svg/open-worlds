package wcp

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os/exec"
	"strings"
	"time"
)

// Client is the WCP/0.1 client. Same six operations as every other SDK.
type Client struct {
	BaseURL string
	HTTP    *http.Client
}

func NewClient(baseURL string) *Client {
	return &Client{
		BaseURL: strings.TrimRight(baseURL, "/"),
		HTTP:    &http.Client{Timeout: 10 * time.Second},
	}
}

func (c *Client) GetManifest() (Manifest, error) {
	var m Manifest
	err := c.get("/manifest", &m)
	return m, err
}

func (c *Client) Petition(req PetitionRequest) (PetitionResponse, error) {
	var r PetitionResponse
	err := c.post("/petition", req, &r)
	return r, err
}

func (c *Client) Act(req ActRequest) (ActResponse, error) {
	var r ActResponse
	err := c.post("/act", req, &r)
	return r, err
}

func (c *Client) GetLog(since string) ([]LogEntry, error) {
	path := "/log"
	if since != "" {
		path += "?since=" + url.QueryEscape(since)
	}
	var wrapper struct {
		Entries []LogEntry `json:"entries"`
	}
	err := c.get(path, &wrapper)
	return wrapper.Entries, err
}

// RunConformance invokes the canonical Python conformance CLI.
// The invocation is identical in every SDK. Conformance lives in
// one place; every language inherits it.
func RunConformance(entityURL string) (bool, []string, error) {
	cmd := exec.Command("python", "-m", "wcp_conformance",
		"--url", entityURL, "--quiet")
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err == nil {
		return true, nil, nil
	}
	var failures []string
	if s := strings.TrimSpace(stdout.String()); s != "" {
		failures = append(failures, s)
	}
	if s := strings.TrimSpace(stderr.String()); s != "" {
		failures = append(failures, s)
	}
	if len(failures) == 0 {
		failures = append(failures, err.Error())
	}
	return false, failures, nil
}

func (c *Client) get(path string, out any) error {
	resp, err := c.HTTP.Get(c.BaseURL + path)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("%s: %s", path, readError(resp.Body))
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

func (c *Client) post(path string, body, out any) error {
	b, err := json.Marshal(body)
	if err != nil {
		return err
	}
	resp, err := c.HTTP.Post(c.BaseURL+path, "application/json", bytes.NewReader(b))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("%s: %s", path, readError(resp.Body))
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

func readError(body io.Reader) string {
	var e struct {
		Error string `json:"error"`
	}
	if json.NewDecoder(body).Decode(&e) == nil && e.Error != "" {
		return e.Error
	}
	return "unknown error"
}
