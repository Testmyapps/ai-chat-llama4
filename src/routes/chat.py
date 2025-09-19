import os
import json
from flask import Blueprint, request, Response, stream_with_context
from openai import OpenAI

chat_bp = Blueprint('chat', __name__)

# إعداد عميل OpenAI للاتصال بـ Baseten
client = OpenAI(
    api_key='3Tel3ATX.p5yn6x9Z07DisZW9D6IEBLCJXJ0VnBZD',
    base_url='https://inference.baseten.co/v1',
)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        previous_messages = data.get('messages', [])
        
        if not user_message:
            return {'error': 'لا توجد رسالة'}, 400
        
        # تحضير رسائل المحادثة
        messages = []
        
        # إضافة رسالة النظام
        messages.append({
            "role": "system",
            "content": "أنت مساعد ذكي مفيد ومهذب. تجيب باللغة العربية بشكل واضح ومفصل. كن مفيدًا ومساعدًا في جميع الأوقات."
        })
        
        # إضافة الرسائل السابقة (آخر 10 رسائل فقط لتوفير الذاكرة)
        for msg in previous_messages[-10:]:
            if msg.get('role') in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # إضافة الرسالة الحالية
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        def generate():
            try:
                # إرسال الطلب إلى نموذج Llama-4
                response = client.chat.completions.create(
                    model="meta-llama/Llama-4-Scout-17B-16E-Instruct",
                    messages=messages,
                    stream=True,
                    stream_options={
                        "include_usage": True,
                        "continuous_usage_stats": True
                    },
                    max_tokens=1000,
                    temperature=0.7,
                    top_p=0.9,
                    presence_penalty=0,
                    frequency_penalty=0
                )
                
                # إرسال الاستجابة المتدفقة
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            # إرسال البيانات بتنسيق Server-Sent Events
                            yield f"data: {json.dumps({'content': delta.content}, ensure_ascii=False)}\n\n"
                
                # إرسال إشارة انتهاء
                yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                print(f"خطأ في توليد الاستجابة: {e}")
                yield f"data: {json.dumps({'error': 'حدث خطأ في توليد الاستجابة'}, ensure_ascii=False)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            }
        )
        
    except Exception as e:
        print(f"خطأ في معالجة الطلب: {e}")
        return {'error': 'حدث خطأ في الخادم'}, 500

@chat_bp.route('/chat', methods=['OPTIONS'])
def chat_options():
    """معالجة طلبات CORS preflight"""
    return '', 200, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }

