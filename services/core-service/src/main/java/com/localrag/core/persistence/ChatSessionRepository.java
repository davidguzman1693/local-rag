package com.localrag.core.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChatSessionRepository extends JpaRepository<ChatSessionEntity, String> {

    List<ChatSessionEntity> findAllByOrderByUpdatedAtDesc();
}

