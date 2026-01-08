#!/bin/bash

echo "🧪 Testing AI-Augmented Personal Archive Services"
echo "================================================="

echo ""
echo "1. 🎨 Gallery Curation Demo"
echo "----------------------------"
python examples/gallery_curation_demo.py

echo ""
echo "2. 🧠 Memory Resurfacing Demo"  
echo "-----------------------------"
python examples/memory_resurfacing_demo.py

echo ""
echo "3. 🔍 Self-Reflection Analysis Demo"
echo "-----------------------------------"
python examples/self_reflection_demo.py

echo ""
echo "4. 🛡️ Privacy & Safety Demo"
echo "---------------------------"
python examples/privacy_safety_demo.py

echo ""
echo "5. 🏃‍♂️ Running Core Tests"
echo "-------------------------"
python -m pytest tests/test_story_generation.py -v
python -m pytest tests/test_people_intelligence.py -v
python -m pytest tests/test_gallery_curation.py -v

echo ""
echo "✅ All service tests completed!"
echo "   To run the full app: ./start_app.sh"