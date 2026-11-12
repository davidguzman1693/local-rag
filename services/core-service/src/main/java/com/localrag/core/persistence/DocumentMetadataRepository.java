package com.localrag.core.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentMetadataRepository extends JpaRepository<DocumentMetadataEntity, String> {
}

