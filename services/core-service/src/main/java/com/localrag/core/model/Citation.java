package com.localrag.core.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record Citation(
        int citationId,
        String documentId,
        String sourceFilename,
        int chunkIndex,
        Integer pageNumber,
        String snippet,
        double relevanceScore
) {}

