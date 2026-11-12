package com.localrag.core.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record ModelDetails(
        @JsonProperty("parameter_size") String parameterSize,
        @JsonProperty("quantization_level") String quantizationLevel,
        @JsonProperty("family") String family
) {}

