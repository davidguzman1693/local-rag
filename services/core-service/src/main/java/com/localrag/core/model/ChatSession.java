package com.localrag.core.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.time.Instant;
import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record ChatSession(
        String id,
        String title,
        Instant createdAt,
        Instant updatedAt,
        List<ChatMessage> messages
) {}

