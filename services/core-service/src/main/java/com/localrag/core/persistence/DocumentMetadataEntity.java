package com.localrag.core.persistence;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "document_metadata")
public class DocumentMetadataEntity {

    @Id
    @Column(name = "document_id", length = 64)
    private String documentId;

    @Column(name = "source_filename", nullable = false)
    private String sourceFilename;

    @Column(name = "file_size_bytes")
    private Long fileSizeBytes;

    @Column(name = "uploaded_at", nullable = false)
    private Instant uploadedAt;

    protected DocumentMetadataEntity() {
    }

    public DocumentMetadataEntity(
            String documentId,
            String sourceFilename,
            Long fileSizeBytes,
            Instant uploadedAt
    ) {
        this.documentId = documentId;
        this.sourceFilename = sourceFilename;
        this.fileSizeBytes = fileSizeBytes;
        this.uploadedAt = uploadedAt;
    }

    public String getDocumentId() {
        return documentId;
    }

    public String getSourceFilename() {
        return sourceFilename;
    }

    public Long getFileSizeBytes() {
        return fileSizeBytes;
    }

    public Instant getUploadedAt() {
        return uploadedAt;
    }
}

