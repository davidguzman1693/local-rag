package com.localrag.core.controller;

import com.localrag.core.model.ChatSession;
import com.localrag.core.model.CreateSessionRequest;
import com.localrag.core.service.ChatSessionService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/sessions")
public class SessionController {

    private final ChatSessionService chatSessionService;

    public SessionController(ChatSessionService chatSessionService) {
        this.chatSessionService = chatSessionService;
    }

    @GetMapping
    public List<ChatSession> listSessions() {
        return chatSessionService.listSessions();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ChatSession createSession(@RequestBody(required = false) CreateSessionRequest request) {
        String title = request != null ? request.title() : null;
        return chatSessionService.createSession(title);
    }

    @GetMapping("/{sessionId}")
    public ChatSession getSession(@PathVariable String sessionId) {
        return chatSessionService.getSession(sessionId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Session not found: " + sessionId));
    }

    @DeleteMapping("/{sessionId}")
    public Map<String, Object> deleteSession(@PathVariable String sessionId) {
        boolean deleted = chatSessionService.deleteSession(sessionId);
        if (!deleted) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Session not found: " + sessionId);
        }
        return Map.of("message", "Session " + sessionId + " deleted successfully.");
    }
}

