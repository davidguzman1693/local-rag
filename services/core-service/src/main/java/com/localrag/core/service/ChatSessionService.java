package com.localrag.core.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.localrag.core.model.ChatMessage;
import com.localrag.core.model.ChatSession;
import com.localrag.core.model.Citation;
import com.localrag.core.persistence.ChatMessageEntity;
import com.localrag.core.persistence.ChatSessionEntity;
import com.localrag.core.persistence.ChatSessionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
public class ChatSessionService {

    private final ChatSessionRepository sessionRepository;
    private final ObjectMapper objectMapper;

    public ChatSessionService(ChatSessionRepository sessionRepository, ObjectMapper objectMapper) {
        this.sessionRepository = sessionRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public ChatSession createSession(String title) {
        String id = UUID.randomUUID().toString();
        Instant now = Instant.now();
        String resolvedTitle = (title != null && !title.isBlank()) ? title.trim() : "New Conversation";
        ChatSessionEntity entity = new ChatSessionEntity(id, resolvedTitle, now, now);
        ChatSessionEntity saved = sessionRepository.save(entity);
        return toModel(saved);
    }

    @Transactional
    public ChatSession getOrCreateSession(String sessionId, String fallbackTitle) {
        if (sessionId != null && !sessionId.isBlank()) {
            Optional<ChatSessionEntity> existing = sessionRepository.findById(sessionId);
            if (existing.isPresent()) {
                return toModel(existing.get());
            }
        }
        String title = fallbackTitle != null && fallbackTitle.length() > 48
                ? fallbackTitle.substring(0, 48) + "..."
                : fallbackTitle;
        return createSession(title);
    }

    @Transactional(readOnly = true)
    public List<ChatSession> listSessions() {
        return sessionRepository.findAllByOrderByUpdatedAtDesc().stream()
                .map(this::toModel)
                .toList();
    }

    @Transactional(readOnly = true)
    public Optional<ChatSession> getSession(String sessionId) {
        return sessionRepository.findById(sessionId).map(this::toModel);
    }

    @Transactional
    public boolean deleteSession(String sessionId) {
        if (!sessionRepository.existsById(sessionId)) {
            return false;
        }
        sessionRepository.deleteById(sessionId);
        return true;
    }

    @Transactional
    public ChatSession appendExchange(
            String sessionId,
            String userQuery,
            String assistantAnswer,
            List<Citation> citations
    ) {
        ChatSessionEntity entity = sessionRepository.findById(sessionId)
                .orElseGet(() -> {
                    Instant now = Instant.now();
                    String title = userQuery != null && userQuery.length() > 48
                            ? userQuery.substring(0, 48) + "..."
                            : (userQuery != null ? userQuery : "New Conversation");
                    return new ChatSessionEntity(
                            sessionId != null && !sessionId.isBlank() ? sessionId : UUID.randomUUID().toString(),
                            title,
                            now,
                            now
                    );
                });

        Instant now = Instant.now();
        entity.addMessage(new ChatMessageEntity(
                UUID.randomUUID().toString(),
                "user",
                userQuery,
                "[]",
                now
        ));

        entity.addMessage(new ChatMessageEntity(
                UUID.randomUUID().toString(),
                "assistant",
                assistantAnswer,
                serializeCitations(citations),
                Instant.now()
        ));

        if ("New Conversation".equals(entity.getTitle()) && userQuery != null && !userQuery.isBlank()) {
            entity.setTitle(userQuery.length() > 48 ? userQuery.substring(0, 48) + "..." : userQuery);
        }
        entity.setUpdatedAt(Instant.now());

        ChatSessionEntity saved = sessionRepository.save(entity);
        return toModel(saved);
    }

    private ChatSession toModel(ChatSessionEntity entity) {
        List<ChatMessage> messages = entity.getMessages().stream()
                .map(msg -> new ChatMessage(
                        msg.getId(),
                        msg.getRole(),
                        msg.getContent(),
                        deserializeCitations(msg.getCitationsJson()),
                        msg.getTimestamp()
                ))
                .toList();

        return new ChatSession(
                entity.getId(),
                entity.getTitle(),
                entity.getCreatedAt(),
                entity.getUpdatedAt(),
                messages
        );
    }

    private String serializeCitations(List<Citation> citations) {
        if (citations == null || citations.isEmpty()) {
            return "[]";
        }
        try {
            return objectMapper.writeValueAsString(citations);
        } catch (Exception e) {
            return "[]";
        }
    }

    private List<Citation> deserializeCitations(String json) {
        if (json == null || json.isBlank()) {
            return List.of();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<List<Citation>>() {});
        } catch (Exception e) {
            return List.of();
        }
    }
}
