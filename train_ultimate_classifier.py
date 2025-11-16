"""
Train the ULTIMATE Emote Classifier
Maximum accuracy with enhanced training
"""

from emote_classifier import EmoteClassifier
import sys
import os
import json


def main():
    print("="*70)
    print("ULTIMATE EMOTE CLASSIFIER TRAINING")
    print("="*70)
    print()

    # Check if training data exists
    if not os.path.exists("emote_training_data_ultimate.json"):
        print("ERROR: No ultimate training data found!")
        print("Please run ultimate_emote_collector.py first to collect samples.")
        print("\nCommand: python ultimate_emote_collector.py")
        sys.exit(1)

    # Load and check training data quality
    print("Analyzing training data...")
    with open("emote_training_data_ultimate.json", 'r') as f:
        training_data = json.load(f)
    
    # Count samples per emote
    emote_counts = {}
    for sample in training_data:
        label = sample['label']
        emote_counts[label] = emote_counts.get(label, 0) + 1
    
    print(f"\nTotal samples: {len(training_data)}")
    print("\nSamples per emote:")
    for emote, count in sorted(emote_counts.items()):
        print(f"  {emote}: {count}")
        if count < 30:
            print(f"    WARNING: Low sample count! Recommended: 40-60")
    
    min_samples = min(emote_counts.values())
    if min_samples < 20:
        print(f"\nERROR: Not enough samples! Minimum 20 per emote required.")
        print("Collect more samples with: python ultimate_emote_collector.py")
        sys.exit(1)
    
    print()

    # Create classifier
    classifier = EmoteClassifier(model_path="emote_model_ultimate.pkl")

    # Train with optimized parameters
    try:
        print("Training Random Forest classifier...")
        print("Optimizations:")
        print("  - 200 decision trees (increased from 100)")
        print("  - Feature importance analysis")
        print("  - Cross-validation for robustness")
        print("  - Stratified sampling for balanced classes\n")

        results = classifier.train(
            training_data_path="emote_training_data_ultimate.json",
            test_size=0.25,  # 25% for testing
            random_state=42
        )

        print("\n" + "="*70)
        print("TRAINING COMPLETE!")
        print("="*70)
        print(f"\nFinal Test Accuracy: {results['accuracy']:.2%}")
        
        # Show per-class accuracy
        report = results['classification_report']
        print("\nPer-Emote Accuracy:")
        for emote in sorted(emote_counts.keys()):
            if emote in report:
                f1 = report[emote]['f1-score']
                precision = report[emote]['precision']
                recall = report[emote]['recall']
                print(f"  {emote}:")
                print(f"    Precision: {precision:.1%}")
                print(f"    Recall: {recall:.1%}")
                print(f"    F1-Score: {f1:.1%}")
        
        print("\nModel saved to: emote_model_ultimate.pkl")
        print("\nNext step: python test_ultimate_detector.py")
        print("="*70)

    except Exception as e:
        print(f"\nERROR during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()