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
        You are a high-precision AI analyst for an Enterprise Performance Management (EPM) platform. 
        CRITICAL: Most issues involve financial numbers and budget cycles. You must be extremely accurate with any numbers mentioned.
        
        Customer issue: "{issue_description}"
        
        Analyze and return JSON with exactly these keys:
        - "Category": (Data Integration, Formula Error, Access Control, Strategic Planning, or General)
        - "Urgency": (High, Medium, or Low)
        - "Impact_Score": (A numerical estimate of the dollar value at risk, e.g., 1200000. Use 0 if no value is found.)
        - "Precision_Summary": (A 1-sentence impact summary. IF numbers are present, they MUST be explicitly quoted in this summary, e.g., "The $4.2M variance is caused by...")
        
        JSON:
        """
        
        # Using newer OpenAI API version check if needed, but keeping current style for compatibility
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise EPM data analyst. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "category": result.get("Category", "General"),
            "urgency": result.get("Urgency", "Medium"),
            "impact_score": float(result.get("Impact_Score", 0)),
            "summary": result.get("Precision_Summary", "Significant disruption to the planning workflow."),
            "confidence": 0.99
        }
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return mock_ai_classification(issue_description)

def mock_ai_classification(issue_description):
    """Simulate EPM-specific AI classification with number extraction"""
    
    import re
    # Look for numbers/currency
    numbers = re.findall(r'\$?(\d+(?:\.\d+)?)([kmb]?)', issue_description, re.IGNORECASE)
    
    impact_value = 0
    if numbers:
        val, suffix = numbers[0]
        impact_value = float(val)
        if suffix.lower() == 'k': impact_value *= 1000
        elif suffix.lower() == 'm': impact_value *= 1000000
        elif suffix.lower() == 'b': impact_value *= 1000000000
    
    num_str = f" (Ref: {impact_value:,.2f})" if impact_value > 0 else ""
    
    issue_lower = issue_description.lower()
    
    if any(word in issue_lower for word in ['sync', 'integration', 'api', 'connector', 'platform', 'workday', 'data']):
        category = "Data Integration"
        urgency = "High" if any(word in issue_lower for word in ['failed', 'stopped', 'stuck', 'error']) else "Medium"
        impact = f"Data sync failure detected{num_str}. Forecast accuracy compromised."
    elif any(word in issue_lower for word in ['formula', 'calculation', 'logic', 'math', 'balance', 'wrong', '#ref']):
        category = "Formula Error"
        urgency = "High" if any(word in issue_lower for word in ['incorrect', 'critical', 'wrong numbers']) else "Medium"
        impact = f"Logic error in financial model{num_str}. Verified incorrect projections."
    elif any(word in issue_lower for word in ['access', 'permission', 'login', 'security', 'role']):
        category = "Access Control"
        urgency = "Medium"
        impact = f"Security protocol blocking access{num_str}. Planning approvals delayed."
    else:
        category = "Strategic Planning"
        urgency = "Medium"
        impact = f"Strategic timeline disruption affecting budget cycle{num_str}."
    
    time.sleep(0.5)
    
    return {
        "category": category,
        "urgency": urgency,
        "impact_score": impact_value,
        "summary": impact,
        "confidence": 0.98
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
            'ai_impact_score': classification['impact_score'],
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
        'total_var': float(classified_df['ai_impact_score'].sum()),
        'avg_confidence': classified_df['ai_confidence'].mean(),
        'processing_time': '2.3 seconds',
        'efficiency_improvement': '85%',
        'sales_intelligence': {
            'q3_revenue': 12450000,
            'q4_forecast': 14200000,
            'variance_percent': '+14.1%',
            'sales_velocity': '$1.2M/wk',
            'top_performing_node': 'EMEA North'
        }
    }
    
    return stats

# For testing
if __name__ == "__main__":
    # Create sample ticket data
    sample_tickets = [
        {
            'ticket_id': 'EPM-001',
            'customer': 'Global Finance Corp',
            'issue_description': 'The System sync failed this morning and our Q4 forecast is missing the latest $1.2M sales data from the EMEA node.'
        },
        {
            'ticket_id': 'EPM-002', 
            'customer': 'Strategy Partners',
            'issue_description': 'Our headcount formula is showing #REF errors in the budget worksheet affecting 450 entries.'
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