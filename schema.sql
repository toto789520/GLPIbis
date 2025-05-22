-- Structure de la base de données pour le système de tickets

-- Table des tickets
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity INTEGER DEFAULT 5,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    assigned_to INTEGER,
    parent_ticket_id INTEGER,
    tags TEXT,
    FOREIGN KEY (user_id) REFERENCES USEUR(ID),
    FOREIGN KEY (assigned_to) REFERENCES USEUR(ID),
    FOREIGN KEY (parent_ticket_id) REFERENCES tickets(id)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_severity ON tickets(severity);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON tickets(assigned_to);

-- Table des commentaires
CREATE TABLE IF NOT EXISTS ticket_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    severity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (user_id) REFERENCES USEUR(ID)
);

CREATE INDEX IF NOT EXISTS idx_comments_ticket ON ticket_comments(ticket_id);

-- Table des associations ticket-matériel
CREATE TABLE IF NOT EXISTS ticket_hardware (
    ticket_id INTEGER NOT NULL,
    hardware_id INTEGER NOT NULL,
    associated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticket_id, hardware_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (hardware_id) REFERENCES hardware(id)
);

-- Triggers pour la mise à jour automatique
CREATE TRIGGER IF NOT EXISTS update_ticket_timestamp 
AFTER UPDATE ON tickets
BEGIN
    UPDATE tickets SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Vue pour les statistiques des tickets
CREATE VIEW IF NOT EXISTS ticket_stats AS
SELECT 
    COUNT(*) as total_tickets,
    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_tickets,
    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_tickets,
    SUM(CASE WHEN severity >= 8 THEN 1 ELSE 0 END) as high_priority_tickets,
    AVG(CASE 
        WHEN status = 'closed' 
        THEN CAST((julianday(closed_at) - julianday(created_at)) * 24 AS INTEGER)
        ELSE NULL 
    END) as avg_resolution_time_hours
FROM tickets; 