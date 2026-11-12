package com.localrag.core.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record RetrievalStageItem(
        @JsonProperty("chunk_id") String chunkId,
        @JsonProperty("document_id") String documentId,
        @JsonProperty("source_filename") String sourceFilename,
        @JsonProperty("chunk_index") int chunkIndex,
        @JsonProperty("page_number") int pageNumber,
        @JsonProperty("text") String text,
        @JsonProperty("rank") int rank,
        @JsonProperty("score") double score,
        @JsonProperty("dense_rank") Integer denseRank,
        @JsonProperty("bm25_rank") Integer bm25Rank
) {}

