import openai
from flask import current_app
import logging
import json
import httpx

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY')

        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in configuration. Please set your OpenAI API key.")

        try:
            # Create a custom HTTPX client to bypass proxy issues
            http_client = httpx.Client(
                timeout=30.0,
                follow_redirects=True
            )

            # Create OpenAI client with our custom HTTP client
            self.client = openai.OpenAI(
                api_key=api_key,
                http_client=http_client
            )

        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def analyze_email(self, email_data):
        """
        Analyze email content using LLM
        
        Args:
            email_data (dict): Parsed email data
            
        Returns:
            dict: Analysis results
        """
        try:
            # Prepare email content for analysis
            content = self._prepare_email_content(email_data)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(content)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                #model="68cfbae2552c81919066195a03170438-stayontop",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            logger.debug("content: " + content)
            logger.debug("System Prompt: " + self._get_system_prompt())
            logger.debug("Prompt: " + prompt)
            
            # Parse response
            analysis_text = response.choices[0].message.content
            analysis = self._parse_analysis_response(analysis_text)
            
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return self._get_default_analysis()
    
    def _prepare_email_content(self, email_data):
        """Prepare email content for LLM analysis"""
        content = {
            'sender': email_data.get('sender', ''),
            'subject': email_data.get('subject', ''),
            'body': email_data.get('body_text', '')[:3000],  # Limit body length
            'has_attachments': email_data.get('has_attachments', False)
        }
        return content
    
    def _get_system_prompt(self):
        """Get system prompt for email analysis"""
        return """
You are a personal assistant that is in charge of going through my emails. Your job is to make sure I do not miss any critical action items or payments, based on the email content.
You will review the input email text and return the following info:
From, Title, Priority from 0 to 5, Dollar amount if available and Deadline. Priority 0 is the lowest, for spam or promotional emails. Priority 5 is Urgent, act now.  
Return should be in a Json format. 
Example:
{ "From": "Gabby", "Title":"Insurance Payment","Priority":4,"Dollar amount":50, "Deadline":"10/02/2025"
}
"""
    
    def _create_analysis_prompt(self, content):
        """Create analysis prompt from email content"""
        return f"""
Please analyze this email:

From: {content['sender']}
Subject: {content['subject']}
Has Attachments: {content['has_attachments']}

Body:
{content['body']}

Provide the analysis in the requested JSON format.
"""
    
    def _parse_analysis_response(self, response_text):
        """Parse LLM response into structured data"""
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                analysis = json.loads(json_text)
                
                # Validate and clean analysis
                return {
                    'sentiment': self._validate_sentiment(analysis.get('sentiment')),
                    'priority': self._validate_priority(analysis.get('priority')),
                    'category': self._validate_category(analysis.get('category')),
                    'summary': str(analysis.get('summary', ''))[:500],
                    'action_required': bool(analysis.get('action_required', False)),
                    'key_points': analysis.get('key_points', [])[:3]
                }
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Error parsing LLM response: {e}")
        
        return self._get_default_analysis()
    
    def _validate_sentiment(self, sentiment):
        """Validate sentiment value"""
        valid_sentiments = ['positive', 'neutral', 'negative']
        return sentiment if sentiment in valid_sentiments else 'neutral'
    
    def _validate_priority(self, priority):
        """Validate priority value"""
        valid_priorities = ['high', 'medium', 'low']
        return priority if priority in valid_priorities else 'medium'
    
    def _validate_category(self, category):
        """Validate category value"""
        valid_categories = ['work', 'personal', 'promotional', 'notification', 'other']
        return category if category in valid_categories else 'other'
    
    def _get_default_analysis(self):
        """Get default analysis when LLM fails"""
        return {
            'sentiment': 'neutral',
            'priority': 'medium',
            'category': 'other',
            'summary': 'Email analysis unavailable',
            'action_required': False,
            'key_points': []
        }
    
    def summarize_multiple_emails(self, emails, limit=10):
        """
        Create a summary of multiple emails
        
        Args:
            emails (list): List of email data
            limit (int): Maximum emails to include in summary
            
        Returns:
            dict: Summary information
        """
        try:
            # Limit emails for processing
            emails_to_process = emails[:limit]
            
            # Prepare content
            email_summaries = []
            for email in emails_to_process:
                email_summaries.append({
                    'sender': email.get('sender', ''),
                    'subject': email.get('subject', ''),
                    'summary': email.get('summary', '')
                })
            
            prompt = f"""
Analyze these {len(email_summaries)} emails and provide:
1. Overall trends or themes
2. Most important/urgent items
3. Summary of action items needed

Emails:
{json.dumps(email_summaries, indent=2)}

Provide a brief summary (2-3 paragraphs).
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                #model="68cfbae2552c81919066195a03170438-stayontop",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            return {
                'summary': response.choices[0].message.content,
                'email_count': len(emails_to_process),
                'total_emails': len(emails)
            }
            
        except Exception as e:
            logger.error(f"Error in email summary: {e}")
            return {
                'summary': 'Summary unavailable',
                'email_count': len(emails),
                'total_emails': len(emails)
            }

    def analyze_email_content(self, email_content, custom_prompt):
        """
        Analyze email content with custom prompt using ChatGPT

        Args:
            email_content (str): Email content including headers and body
            custom_prompt (str): Custom prompt for analysis

        Returns:
            str: ChatGPT response
        """
        try:
            # Create the full prompt
            full_prompt = f"""
{custom_prompt}

Email Content:
{email_content}
"""
            system_prompt = self._get_system_prompt()
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                #model="68cfbae2552c81919066195a03170438-stayontop",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],

                temperature=0.3,
                max_tokens=1000
            )
      
            logger.debug("System Prompt: " + self._get_system_prompt())
            logger.debug("Full_prompt: " + full_prompt)

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in analyze_email_content: {e}")
            raise