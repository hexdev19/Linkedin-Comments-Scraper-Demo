from openai import OpenAI
from typing import List
from app.core.config import settings
from app.schemas.comments_scraper import CommentOut

def analyze_comments_logic(comments: List[CommentOut]) -> str:
    if not comments:
        return "No comments to analyze."

    client = OpenAI(api_key=settings.openai_api_key)
    
    comments_text = "\n".join([f"- {c.author}: {c.original_text}" for c in comments])
    
    prompt = f"""
    Analyze the following LinkedIn comments and provide a concise, insightful one-paragraph summary. 
    Focus on the overall sentiment, key topics discussed, and the general vibe of the interaction. 
    Identify if there are any repetitive themes or standout opinions.

    Comments:
    {comments_text}

    Analysis:
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional social media analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()
