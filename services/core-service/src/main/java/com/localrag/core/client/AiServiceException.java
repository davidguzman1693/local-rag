package com.localrag.core.client;

import org.springframework.http.HttpStatusCode;

public class AiServiceException extends RuntimeException {

    private final HttpStatusCode statusCode;

    public AiServiceException(String message, HttpStatusCode statusCode) {
        super(message);
        this.statusCode = statusCode;
    }

    public AiServiceException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = HttpStatusCode.valueOf(502);
    }

    public HttpStatusCode getStatusCode() {
        return statusCode;
    }
}

