package com.localrag.core.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record SearchDebugResponse(
        @JsonProperty("query") String query,
        @JsonProperty("retrieval_time_ms") double retrievalTimeMs,
        @JsonProperty("dense_results") List<RetrievalStageItem> denseResults,
        @JsonProperty("bm25_results") List<RetrievalStageItem> bm25Results,
        @JsonProperty("rrf_results") List<RetrievalStageItem> rrfResults,
        @JsonProperty("reranked_results") List<RetrievalStageItem> rerankedResults
) {}

