package com.localrag.core.service;

import com.localrag.core.model.ChatMessage;
import com.localrag.core.model.ChatSession;
import com.localrag.core.model.Citation;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ChatSessionService {

    private final Map<String, ChatSession> sessions = new ConcurrentHashMap<>();

    public ChatSession createSession(String title) {
        String id = UUID.randomUUID().toString();
        Instant now = Instant.now();
        String resolvedTitle = (title != null && !title.isBlank()) ? title.trim() : "New Conversation";
        ChatSession session = new ChatSession(id, resolvedTitle, now, now, new ArrayList<>());
        sessions.put(id, session);
        return session;
    }

    public ChatSession getOrCreateSession(String sessionId, String fallbackTitle) {
        if (sessionId != null && !sessionId.isBlank() && sessions.containsKey(sessionId)) {
            return sessions.get(sessionId);
        }
        String title = fallbackTitle != null && fallbackTitle.length() > 48
                ? fallbackTitle.substring(0, 48) + "..."
                : fallbackTitle;
        return createSession(title);
    }

    public List<ChatSession> listSessions() {
        return sessions.values().stream()
                .sorted(Comparator.comparing(ChatSession::updatedAt).reversed())
                .toList();
    }

    public Optional<ChatSession> getSession(String sessionId) {
        return Optional.ofNullable(sessions.get(sessionId));
    }

    public boolean deleteSession(String sessionId) {
        return sessions.remove(sessionId) != null;
    }

    public synchronized ChatSession appendExchange(
            String sessionId,
            String userQuery,
            String assistantAnswer,
            List<Citation> citations
    ) {
        ChatSession existing = getOrCreateSession(sessionId, userQuery);
        List<ChatMessage> updatedMessages = new ArrayList<>(existing.messages());

        Instant now = Instant.now();
        updatedMessages.add(new ChatMessage(
                UUID.randomUUID().toString(),
                "user",
                userQuery,
                List.of(),
                now
        ));
        updatedMessages.add(new ChatMessage(
                UUID.randomUUID().toString(),
                "assistant",
                assistantAnswer,
                citations != null ? citations : List.of(),
                Instant.now()
        ));

        String updatedTitle = ("New Conversation".equals(existing.title()) && userQuery != null && !userQuery.isBlank())
                ? (userQuery.length() > 48 ? userQuery.substring(0, 48) + "..." : userQuery)
                : existing.title();

        ChatSession updated = new ChatSession(
                existing.id(),
                updatedTitle,
                existing.createdAt(),
                Instant.now(),
                updatedMessages
        );
        sessions.put(updated.id(), updated);
        return updated;
    }
}

