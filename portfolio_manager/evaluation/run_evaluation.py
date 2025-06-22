import json
import os
from pathlib import Path
from google.adk.evaluation import evaluate_agent
from google.adk.agents import Agent

def load_eval_set(eval_set_path: str):
    """Load evaluation set from JSON file"""
    with open(eval_set_path, 'r') as f:
        return json.load(f)

def run_portfolio_evaluation():
    """Run evaluation on Portfolio Manager Agent"""
    
    # Load the agent
    from portfolio_manager.agent import root_agent
    
    # Load evaluation set
    eval_set_path = Path(__file__).parent / "portfolio_eval_set.json"
    eval_set = load_eval_set(eval_set_path)
    
    print("🧪 Starting Portfolio Manager Agent Evaluation")
    print(f"📊 Evaluation Set: {eval_set['eval_set_name']}")
    print(f"📝 Test Cases: {len(eval_set['eval_cases'])}")
    
    # Run evaluation
    results = evaluate_agent(
        agent=root_agent,
        eval_set=eval_set,
        output_dir="evaluation_results"
    )
    
    # Print summary
    print("\n📈 Evaluation Results Summary:")
    print(f"✅ Passed: {results['passed_cases']}")
    print(f"❌ Failed: {results['failed_cases']}")
    print(f"📊 Overall Score: {results['overall_score']:.2%}")
    
    # Detailed results
    for case_result in results['case_results']:
        case_id = case_result['case_id']
        score = case_result['score']
        status = "✅ PASS" if case_result['passed'] else "❌ FAIL"
        
        print(f"\n{status} {case_id}: {score:.2%}")
        
        if not case_result['passed']:
            print(f"  Issues: {case_result.get('issues', [])}")
    
    return results

if __name__ == "__main__":
    results = run_portfolio_evaluation()




