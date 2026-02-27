class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    text = db.Column(db.Text)
    summary = db.Column(db.Text)
    tags = db.Column(db.String(255))
    embedding = db.Column(db.JSON)

    approved = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def tags_list(self):
        """Returns clean list of tags for UI display"""
        if self.tags:
            return [t.strip() for t in self.tags.split(",") if t.strip()]
        return []

