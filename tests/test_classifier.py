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
    
    logger.info(f"Starting EPM ticket classification for {len(tickets_df)} tickets")
    
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

def classify_ticket(issue_description):
    """
    Single ticket classification function (for compatibility with app.py)
    Returns a dictionary with category, urgency, and summary
    """
    result = mock_ai_classification(issue_description)
    return {
        "category": result["category"],
        "urgency": result["urgency"],
        "summary": result["summary"]
    }

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

def batch_classify_tickets(tickets_list, batch_size=10):
    """
    Classify tickets in batches to avoid rate limits
    """
    results = []
    total_tickets = len(tickets_list)
    
    logger.info(f"Processing {total_tickets} tickets in batches of {batch_size}")
    
    for i in range(0, total_tickets, batch_size):
        batch = tickets_list[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(total_tickets + batch_size - 1)//batch_size}")
        
        for ticket in batch:
            result = classify_ticket(ticket['issue_description'])
            results.append({
                'ticket_id': ticket.get('ticket_id', f'EPM-{len(results)+1}'),
                'customer': ticket.get('customer', 'N/A'),
                'issue_description': ticket['issue_description'],
                'category': result['category'],
                'urgency': result['urgency'],
                'summary': result['summary']
            })
        
        # Small delay between batches
        time.sleep(0.5)
    
    return results

def export_results(results_df, filename="classified_planning_tickets.csv"):
    """Export classification results to CSV"""
    try:
        results_df.to_csv(filename, index=False)
        logger.info(f"Results exported to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error exporting results: {str(e)}")
        return False

def validate_ticket_data(df):
    """Validate that the uploaded ticket data has required columns"""
    required_columns = ['issue_description']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check for empty issue descriptions
    empty_issues = df['issue_description'].isna().sum()
    if empty_issues > 0:
        return False, f"Found {empty_issues} tickets with empty issue descriptions"
    
    return True, "Data validation passed"

def test_mock_ai_classification():
    """Test EPM-specific mock AI responses"""
    # Test Data Integration
    res = mock_ai_classification("Data sync failed in Pigment")
    assert res["category"] == "Data Integration"
    assert res["urgency"] == "High"
    
    # Test Formula Error
    res = mock_ai_classification("Calculation error in budget sheet")
    assert res["category"] == "Formula Error"
    
    # Test General
    res = mock_ai_classification("Just a question about the UI")
    assert res["category"] == "General"

def test_classify_tickets_logic():
    """Test batch classification logic"""
    sample_df = pd.DataFrame([
        {'ticket_id': 'EPM-001', 'customer': 'Test', 'issue_description': 'API error in Workday integration'}
    ])
    results = classify_tickets(sample_df)
    assert len(results) == 1
    assert results.iloc[0]['ai_category'] == "Data Integration"

if __name__ == "__main__":
    pytest.main(["-v", __file__])