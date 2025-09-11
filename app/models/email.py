from datetime import datetime
from app import db

class Email(db.Model):
    __tablename__ = 'emails'
    
    id = db.Column(db.String(100), primary_key=True)  # Gmail message ID
    user_id = db.Column(db.String(100), nullable=False, index=True)
    sender = db.Column(db.String(255), nullable=False, index=True)
    recipient = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(500), nullable=False, index=True)
    body_text = db.Column(db.Text)
    body_html = db.Column(db.Text)
    date_received = db.Column(db.DateTime, nullable=False, index=True)
    date_processed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # LLM Analysis Results
    sentiment = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    category = db.Column(db.String(100))
    summary = db.Column(db.Text)
    action_required = db.Column(db.Boolean, default=False)
    
    # Email metadata
    thread_id = db.Column(db.String(100), index=True)
    has_attachments = db.Column(db.Boolean, default=False)
    attachment_count = db.Column(db.Integer, default=0)
    labels = db.Column(db.Text)  # JSON string of Gmail labels
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender': self.sender,
            'recipient': self.recipient,
            'subject': self.subject,
            'body_text': self.body_text,
            'body_html': self.body_html,
            'date_received': self.date_received.isoformat() if self.date_received else None,
            'date_processed': self.date_processed.isoformat() if self.date_processed else None,
            'sentiment': self.sentiment,
            'priority': self.priority,
            'category': self.category,
            'summary': self.summary,
            'action_required': self.action_required,
            'thread_id': self.thread_id,
            'has_attachments': self.has_attachments,
            'attachment_count': self.attachment_count,
            'labels': self.labels
        }
    
    def to_summary_dict(self):
        return {
            'id': self.id,
            'sender': self.sender,
            'subject': self.subject,
            'date_received': self.date_received.isoformat() if self.date_received else None,
            'priority': self.priority,
            'category': self.category,
            'summary': self.summary,
            'action_required': self.action_required,
            'has_attachments': self.has_attachments
        }