"""
Deep diagnostic script for LLM query generation across all agents.
Tests actual Gemini responses and parsing behavior.
"""
import sys
sys.path.insert(0, 'src')

import json
import time
from hw4_tourguide.config_loader import ConfigLoader
from hw4_tourguide.tools.llm_client import llm_factory
from hw4_tourguide.tools.prompt_loader import load_prompt_with_context


def print_section(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def test_agent_llm_response(agent_type, task, config_loader):
    """Test LLM query generation for a specific agent type."""
    print_section(f"TESTING {agent_type.upper()} AGENT")

    # Get config for this agent type
    if agent_type == 'judge':
        config = config_loader.get_all()['judge']
    else:
        config = config_loader.get_all()['agents']

    # Create LLM client
    llm_client = llm_factory(config, config_loader.get_secret)

    # Prepare context for prompt
    ctx = dict(task)
    ctx.setdefault("search_limit", 3)

    print(f"\n📋 Task Context:")
    print(f"   Location: {task.get('location_name')}")
    print(f"   Search Hint: {task.get('search_hint')}")
    print(f"   Route Context: {task.get('route_context')}")

    # Load prompt
    prompt = load_prompt_with_context(agent_type, ctx)
    print(f"\n📝 Prompt Length: {len(prompt)} characters")
    print(f"   First 200 chars: {prompt[:200]}...")

    # Call LLM
    print(f"\n🔄 Calling Gemini LLM...")
    start = time.time()
    response = llm_client.query(prompt)
    duration = time.time() - start

    text = response.get('text', '')
    print(f"\n⏱️  Response Time: {duration:.2f}s")
    print(f"\n📤 RAW LLM RESPONSE:")
    print("-" * 80)
    print(text)
    print("-" * 80)

    # Test parsing strategies
    print(f"\n🔍 PARSING ANALYSIS:")

    # Strategy 1: Direct JSON parse
    print("\n   Strategy 1: Direct json.loads()")
    try:
        parsed = json.loads(text)
        print(f"   ✅ SUCCESS - Type: {type(parsed).__name__}")

        if isinstance(parsed, dict):
            print(f"      Keys: {list(parsed.keys())}")
            print(f"      'queries' field: {parsed.get('queries')}")
            print(f"      'search_queries' field: {parsed.get('search_queries')}")
            print(f"      'reasoning' field: {parsed.get('reasoning', '')[:100] if parsed.get('reasoning') else 'None'}...")
        elif isinstance(parsed, list):
            print(f"      ⚠️  RETURNED LIST instead of DICT")
            print(f"      List length: {len(parsed)}")
            print(f"      List items: {parsed}")
            print(f"      💡 This is the issue! LLM returned flat list instead of {{'queries': [...], 'reasoning': '...'}}")
    except json.JSONDecodeError as e:
        print(f"   ❌ FAILED - {e}")

    # Strategy 2: Markdown code fence removal
    print("\n   Strategy 2: Strip markdown fences")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

        try:
            parsed = json.loads(cleaned)
            print(f"   ✅ SUCCESS after fence removal - Type: {type(parsed).__name__}")
            if isinstance(parsed, list):
                print(f"      ⚠️  Still a list! Length: {len(parsed)}")
        except json.JSONDecodeError as e:
            print(f"   ❌ FAILED - {e}")
    else:
        print(f"   ℹ️  No markdown fences detected")

    # Test _convert_array_to_dict logic
    print("\n   Testing Array-to-Dict Conversion:")
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, list):
            print(f"   📦 Applying _convert_array_to_dict logic...")
            queries = []
            reasoning_parts = []

            for item in parsed:
                if isinstance(item, str):
                    if item.strip():
                        queries.append(item.strip())
                elif isinstance(item, dict):
                    query = item.get("query", "")
                    if query:
                        queries.append(query)
                    reason = item.get("rationale") or item.get("reasoning") or item.get("description") or ""
                    if reason:
                        reasoning_parts.append(reason)

            reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Converted from array format"
            converted = {"queries": queries, "reasoning": reasoning}

            print(f"   ✅ Converted successfully:")
            print(f"      Queries: {converted['queries']}")
            print(f"      Reasoning: {converted['reasoning']}")
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")

    print("\n" + "-" * 80)
    return text, parsed if 'parsed' in locals() else None


def main():
    print_section("LLM QUERY GENERATION DIAGNOSTIC")
    print("\nThis script tests actual Gemini responses for all three agents")
    print("to identify if/when it returns flat lists vs. expected dict format.\n")

    config_loader = ConfigLoader()

    # Test task representing a typical route step
    test_task = {
        'location_name': 'MIT',
        'address': '77 Massachusetts Ave, Cambridge, MA',
        'search_hint': 'campus architecture and innovation',
        'route_context': 'Boston to Cambridge university tour',
        'instructions': 'Head north on Massachusetts Ave toward Memorial Drive',
        'coordinates': {'lat': 42.3601, 'lng': -71.0942},
        'search_limit': 3
    }

    # Test all three agents
    results = {}

    for agent_type in ['video', 'knowledge', 'song']:
        try:
            raw, parsed = test_agent_llm_response(agent_type, test_task, config_loader)
            results[agent_type] = {
                'raw': raw,
                'parsed': parsed,
                'is_list': isinstance(parsed, list) if parsed else False,
                'is_dict': isinstance(parsed, dict) if parsed else False
            }
        except Exception as e:
            print(f"\n❌ ERROR testing {agent_type}: {e}")
            import traceback
            traceback.print_exc()
            results[agent_type] = {'error': str(e)}

    # Summary
    print_section("DIAGNOSTIC SUMMARY")

    for agent_type, result in results.items():
        if 'error' in result:
            print(f"\n❌ {agent_type.upper()}: ERROR - {result['error']}")
        else:
            status = "✅ DICT (correct)" if result['is_dict'] else "⚠️  LIST (problematic)"
            print(f"\n{status} - {agent_type.upper()}")
            if result['is_list']:
                print(f"   🔴 This agent is returning a flat list instead of {{queries: [...], reasoning: '...'}}")
                print(f"   🔧 The _convert_array_to_dict logic should handle this")

    # Check if the issue exists
    problematic = [k for k, v in results.items() if v.get('is_list')]
    if problematic:
        print(f"\n⚠️  ISSUE CONFIRMED:")
        print(f"   Agents returning flat lists: {', '.join(problematic)}")
        print(f"\n💡 RECOMMENDATION:")
        print(f"   1. The code ALREADY has _convert_array_to_dict logic in base_agent.py")
        print(f"   2. Lines 228-232 handle this case in _extract_json_from_response")
        print(f"   3. If errors still occur, the issue may be in _build_queries_with_llm validation")
    else:
        print(f"\n✅ ALL AGENTS RETURNING CORRECT FORMAT")
        print(f"   No flat list responses detected - issue may be intermittent or already fixed")


if __name__ == "__main__":
    main()
