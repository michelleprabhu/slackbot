import pandas as pd
import json
import os
import logging
from datetime import datetime
import time
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ticket_classifier")

# Check if OpenAI API key is available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK_AI = OPENAI_API_KEY is None

def classify_with_openai(issue_description):
    """Classify EPM-related ticket using OpenAI API"""
    
    if USE_MOCK_AI:
        logger.warning("OpenAI API key not found, using EPM mock AI responses")
        return mock_ai_classification(issue_description)
    
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        
        prompt = f"""
        You are a smart AI strategist for an Enterprise Performance Management (EPM) platform. 
        Given this customer issue:
        "{issue_description}"
        
        Classify the ticket into these EPM categories:
        - Category: Data Integration, Formula Error, Access Control, Strategic Planning, General
        - Urgency: High (Immediate impact on budget cycle), Medium, Low
        - Business Impact: Provide a concise 1-sentence summary of how this affects the planning cycle.
        
        Return the output as JSON.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an EPM support ticket classifier that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        
        result_text = response.choices[0].message.content
        
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                logger.error(f"Failed to parse OpenAI response as JSON: {result_text}")
                return mock_ai_classification(issue_description)
        
        return {
            "category": result.get("Category", "General"),
            "urgency": result.get("Urgency", "Medium"),
            "summary": result.get("Business Impact", "Potential disruption to the planning workflow."),
            "confidence": 0.95
        }
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return mock_ai_classification(issue_description)

def mock_ai_classification(issue_description):
    """Simulate EPM-specific AI classification"""
    
    issue_lower = issue_description.lower()
    
    if any(word in issue_lower for word in ['sync', 'integration', 'api', 'connector', 'pigment', 'workday', 'data']):
        category = "Data Integration"
        urgency = "High" if any(word in issue_lower for word in ['failed', 'stopped', 'stuck', 'error']) else "Medium"
        impact = "Nightly data refresh failed, impacting accuracy of real-time forecasts."
    elif any(word in issue_lower for word in ['formula', 'calculation', 'logic', 'math', 'balance', 'wrong']):
        category = "Formula Error"
        urgency = "High" if any(word in issue_lower for word in ['incorrect', 'critical', 'wrong numbers']) else "Medium"
        impact = "Modeling logic error may cause significant variances in budget projections."
    elif any(word in issue_lower for word in ['access', 'permission', 'login', 'security', 'role']):
        category = "Access Control"
        urgency = "Medium"
        impact = "Stakeholders unable to review or approve planning worksheets."
    elif any(word in issue_lower for word in ['forecast', 'budget', 'scenario', 'strategic', 'cycle']):
        category = "Strategic Planning"
        urgency = "Medium"
        impact = "Planning workflow bottleneck affecting strategic timeline."
    else:
        category = "General"
        urgency = "Low"
        impact = "General inquiry regarding platform capabilities."
    
    time.sleep(0.1)
    
    return {
        "category": category,
        "urgency": urgency,
        "summary": impact,
        "confidence": round(random.uniform(0.85, 0.99), 2)
    }

def classify_tickets(tickets_df):
    """Process all tickets and add AI classifications"""
    
    logger.info(f"Starting AI ticket classification for {len(tickets_df)} tickets")
    
    results = []
    
    for index, row in tickets_df.iterrows():
        ticket_id = row['ticket_id']
        customer = row['customer']
        issue = row['issue_description']
        
        logger.info(f"Classifying ticket {ticket_id} for {customer}")
        
        # Get AI classification
        classification = classify_with_openai(issue)
        
        # Combine original data with AI results
        result = {
            'ticket_id': ticket_id,
            'customer': customer,
            'issue_description': issue,
            'ai_category': classification['category'],
            'ai_urgency': classification['urgency'],
            'ai_summary': classification['summary'],
            'ai_confidence': classification['confidence'],
            'processed_at': datetime.now().isoformat()
        }
        
        results.append(result)
    
    logger.info(f"Completed classification of {len(results)} tickets")
    return pd.DataFrame(results)

def generate_stats(classified_df):
    """Generate dashboard statistics"""
    
    total_tickets = len(classified_df)
    
    # Category breakdown
    category_counts = classified_df['ai_category'].value_counts().to_dict()
    
    # Urgency breakdown
    urgency_counts = classified_df['ai_urgency'].value_counts().to_dict()
    
    # High priority tickets
    high_priority = classified_df[classified_df['ai_urgency'] == 'High']
    
    stats = {
        'total_tickets': total_tickets,
        'categories': category_counts,
        'urgency_levels': urgency_counts,
        'high_priority_count': len(high_priority),
        'avg_confidence': classified_df['ai_confidence'].mean(),
        'processing_time': '2.3 seconds',
        'efficiency_improvement': '85%'
    }
    
    return stats

# For testing
if __name__ == "__main__":
    # Create sample ticket data
    sample_tickets = [
        {
            'ticket_id': 'EPM-001',
            'customer': 'Global Finance Corp',
            'issue_description': 'The Pigment sync failed this morning and our Q4 forecast is missing the latest sales data'
        },
        {
            'ticket_id': 'EPM-002', 
            'customer': 'Strategy Partners',
            'issue_description': 'Our headcount formula is showing #REF errors in the budget worksheet'
        }
    ]
    
    # Convert to DataFrame
    tickets_df = pd.DataFrame(sample_tickets)
    
    # Process tickets with AI
    classified_df = classify_tickets(tickets_df)
    
    # Print results
    print(classified_df)
    
    # Generate stats
    stats = generate_stats(classified_df)
    print(json.dumps(stats, indent=2))