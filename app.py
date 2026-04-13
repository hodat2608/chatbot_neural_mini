from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid
from openai import OpenAI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

client = OpenAI(
    api_key="llmapi_a4546db82a22c3667e04399cbfd2b8e9f96158a2637d61a39c8064cc1cb2ed03",
    base_url="https://api.llmapi.ai/v1"
)

# Models
class Conversation(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False, default="New Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    convs = Conversation.query.order_by(Conversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'created_at': c.created_at.isoformat(),
        'updated_at': c.updated_at.isoformat()
    } for c in convs])

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    conv = Conversation(title="New Chat")
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'title': conv.title, 'created_at': conv.created_at.isoformat()})

@app.route('/api/conversations/<conv_id>', methods=['GET'])
def get_conversation(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    msgs = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at).all()
    return jsonify({
        'id': conv.id,
        'title': conv.title,
        'messages': [{'role': m.role, 'content': m.content, 'created_at': m.created_at.isoformat()} for m in msgs]
    })

@app.route('/api/conversations/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/conversations/<conv_id>/rename', methods=['PATCH'])
def rename_conversation(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    data = request.json
    conv.title = data.get('title', conv.title)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/conversations/<conv_id>/clear', methods=['POST'])
def clear_conversation(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    Message.query.filter_by(conversation_id=conv_id).delete()
    conv.title = "New Chat"
    conv.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    conv_id = data.get('conversation_id')
    user_message = data.get('message', '').strip()
    model = data.get('model', 'gpt-4o')

    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    if not conv_id:
        conv = Conversation()
        db.session.add(conv)
        db.session.flush()
        conv_id = conv.id
    else:
        conv = Conversation.query.get_or_404(conv_id)

    # Save user message
    user_msg = Message(conversation_id=conv_id, role='user', content=user_message)
    db.session.add(user_msg)

    # Get history
    history = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at).all()
    messages_payload = [{'role': m.role, 'content': m.content} for m in history]

    def generate():
        full_response = ""
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages_payload,
                stream=True
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_response += delta.content
                    yield f"data: {json.dumps({'type': 'chunk', 'content': delta.content, 'conv_id': conv_id})}\n\n"

            # Save assistant message
            asst_msg = Message(conversation_id=conv_id, role='assistant', content=full_response)
            db.session.add(asst_msg)

            # Auto-title from first message
            if conv.title == "New Chat" and len(history) == 0:
                title = user_message[:50] + ("..." if len(user_message) > 50 else "")
                conv.title = title

            conv.updated_at = datetime.utcnow()
            db.session.commit()
            yield f"data: {json.dumps({'type': 'done', 'conv_id': conv_id, 'title': conv.title})}\n\n"
        except Exception as e:
            db.session.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
