import pandas as pd
import numpy as np

def run_tiered_audit(input_file, output_file):
    """
    Categorizes AI vs Human coding into Tiers to prioritize expert review.
    """
    print(f"📂 Loading {input_file} for tiered audit...")
    df = pd.read_csv(input_file)
    
    def get_code_set(row, source='human'):
        """Helper to extract non-null codes into a set."""
        if source == 'human':
            cols = ['Code 1', 'Code 2', 'Code 3']
            codes = [str(row[c]).strip() for c in cols if pd.notna(row[c]) and str(row[c]).lower() != 'nan']
        else:
            val = row.get('New_AI_Final_Code', '')
            codes = [c.strip() for c in str(val).split(',') if c.strip()]
        return set(codes)

    def classify_tier(row):
        human = get_code_set(row, 'human')
        ai = get_code_set(row, 'ai')
        
        # 1. Perfect Match
        if human == ai and len(human) > 0:
            return 'Match'
        
        # 2. Abandoned/Empty Check
        if not human and not ai:
            return 'Both Empty'
        
        # 3. Tier 1: Total Mismatch (Zero Overlap)
        intersection = human.intersection(ai)
        if not intersection and human and ai:
            return 'Tier 1: Total Mismatch'
        
        # 4. Tier 2: Intent Expansion (AI found everything human did + MORE)
        if human.issubset(ai) and ai != human:
            return 'Tier 2: Intent Expansion'
        
        # 5. Tier 3: Intent Contraction (Human found things AI missed)
        if ai.issubset(human) and ai != human:
            return 'Tier 3: Intent Contraction'
            
        # 6. Complex Overlap (Some overlap, but both have unique additions)
        return 'Complex Overlap'

    # Apply Tiering
    df['Audit_Tier'] = df.apply(classify_tier, axis=1)
    
    # Generate human-readable "Diff" for the auditor
    def generate_diff(row):
        human = get_code_set(row, 'human')
        ai = get_code_set(row, 'ai')
        
        added = ai - human
        missed = human - ai
        
        diff_text = []
        if missed: diff_text.append(f"MISSING IN AI: {', '.join(missed)}")
        if added: diff_text.append(f"ADDED BY AI: {', '.join(added)}")
        
        return " | ".join(diff_text) if diff_text else "Identical"

    df['Audit_Diff_Notes'] = df.apply(generate_diff, axis=1)

    # Sort by Tier Priority for the researcher
    tier_order = [
        'Tier 1: Total Mismatch', 
        'Tier 3: Intent Contraction', 
        'Tier 2: Intent Expansion', 
        'Complex Overlap',
        'Match',
        'Both Empty'
    ]
    df['Audit_Tier'] = pd.Categorical(df['Audit_Tier'], categories=tier_order, ordered=True)
    df = df.sort_values('Audit_Tier')
    
    # Save the Audit File
    df.to_csv(output_file, index=False)
    
    # Print Summary Report
    print("\n--- AUDIT SUMMARY REPORT ---")
    print(df['Audit_Tier'].value_counts().sort_index())
    print(f"\n✅ Audit complete. Review flagged rows in: {output_file}")

if __name__ == "__main__":
    # Point this to your latest AI output file
    run_tiered_audit('Comparison_TestSample_Mismatch.csv', 'Tiered_Consensus_Audit.csv')
