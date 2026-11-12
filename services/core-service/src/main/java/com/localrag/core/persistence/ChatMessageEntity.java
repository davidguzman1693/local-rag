package com.localrag.core.persistence;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "chat_messages")
public class ChatMessageEntity {

    @Id
    @Column(length = 64)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private ChatSessionEntity session;

    @Column(name = "sequence_number", nullable = false)
    private int sequenceNumber;

    @Column(nullable = false, length = 32)
    private String role;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "citations_json", columnDefinition = "TEXT")
    private String citationsJson;

    @Column(nullable = false)
    private Instant timestamp;

    protected ChatMessageEntity() {
    }

    public ChatMessageEntity(
            String id,
            String role,
            String content,
            String citationsJson,
            Instant timestamp
    ) {
        this.id = id;
        this.role = role;
        this.content = content;
        this.citationsJson = citationsJson;
        this.timestamp = timestamp;
    }

    public String getId() {
        return id;
    }

    public ChatSessionEntity getSession() {
        return session;
    }

    public void setSession(ChatSessionEntity session) {
        this.session = session;
    }

    public int getSequenceNumber() {
        return sequenceNumber;
    }

    public void setSequenceNumber(int sequenceNumber) {
        this.sequenceNumber = sequenceNumber;
    }

    public String getRole() {
        return role;
    }

    public String getContent() {
        return content;
    }

    public String getCitationsJson() {
        return citationsJson;
    }

    public Instant getTimestamp() {
        return timestamp;
    }
}

