"""
ElevenLabs API Test Script
Test your ElevenLabs API key and voice generation functionality
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_elevenlabs_basic():
    """Test basic ElevenLabs API connection and voice listing"""
    print("🔍 Testing ElevenLabs API Connection...")
    
    try:
        from elevenlabs.client import ElevenLabs
        
        # Get API key
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ ELEVENLABS_API_KEY environment variable not set")
            print("💡 Set your API key: export ELEVENLABS_API_KEY='your_key_here'")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")
        
        # Initialize client
        client = ElevenLabs(api_key=api_key)
        print("✅ ElevenLabs client initialized successfully")
        
        # Test API connection by listing voices
        print("\n🎤 Fetching available voices...")
        voices = client.voices.get_all()
        
        if voices and hasattr(voices, 'voices'):
            print(f"✅ Found {len(voices.voices)} voices available:")
            for voice in voices.voices[:5]:  # Show first 5 voices
                print(f"   - {voice.name} (ID: {voice.voice_id})")
        else:
            print("⚠️ No voices found or unexpected response format")
            
        return True
        
    except ImportError:
        print("❌ ElevenLabs library not installed")
        print("💡 Install with: pip install elevenlabs")
        return False
    except Exception as e:
        print(f"❌ API Connection failed: {str(e)}")
        print("💡 Check your API key and internet connection")
        return False

def test_voice_generation():
    """Test actual voice generation with a simple text"""
    print("\n🎙️ Testing Voice Generation...")
    
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ API key required for voice generation test")
            return False
        
        client = ElevenLabs(api_key=api_key)
        
        # Test text
        test_text = "Hello! This is a test of the ElevenLabs text-to-speech API. If you can hear this clearly, the integration is working perfectly."
        
        # Voice configuration (using the same voices as your code)
        voice_options = [
            "kdmDKE6EkgrWrrykO9Qt",  # Alexandra
            "PoHUWWWMHFrA8z7Q88pu",  # Miranda
        ]
        
        selected_voice_id = voice_options[0]
        voice_name = "Alexandra"
        
        print(f"🎯 Using voice: {voice_name} (ID: {selected_voice_id})")
        print(f"📝 Test text: '{test_text[:50]}...'")
        
        # Voice settings
        voice_settings = VoiceSettings(
            stability=0.75,
            similarity_boost=0.85,
            style=0.2,
            use_speaker_boost=True
        )
        
        print("⏳ Generating audio...")
        
        # Generate audio
        audio_response = client.text_to_speech.convert(
            text=test_text,
            voice_id=selected_voice_id,
            model_id="eleven_multilingual_v2",
            voice_settings=voice_settings,
            output_format="mp3_44100_128"
        )
        
        # Save test audio file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_filename = f"elevenlabs_test_{timestamp}.mp3"
        
        # Create output directory
        output_dir = Path("./test_audio_output")
        output_dir.mkdir(exist_ok=True)
        
        test_file_path = output_dir / test_filename
        
        with open(test_file_path, "wb") as audio_file:
            audio_file.write(audio_response)
        
        file_size = test_file_path.stat().st_size
        
        print("✅ Audio generation successful!")
        print(f"💾 File saved: {test_file_path}")
        print(f"📊 File size: {file_size:,} bytes")
        print(f"🎵 You can play the file to test audio quality")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice generation failed: {str(e)}")
        print("💡 Common issues:")
        print("   - Invalid API key")
        print("   - Insufficient credits")
        print("   - Network connectivity")
        print("   - Voice ID not available")
        return False

def test_voice_details():
    """Test specific voice details and availability"""
    print("\n🔍 Testing Voice Details...")
    
    try:
        from elevenlabs.client import ElevenLabs
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ API key required")
            return False
        
        client = ElevenLabs(api_key=api_key)
        
        # Test the specific voices used in your code
        voice_ids_to_test = [
            ("Alexandra", "kdmDKE6EkgrWrrykO9Qt"),
            ("Miranda", "PoHUWWWMHFrA8z7Q88pu"),
        ]
        
        for voice_name, voice_id in voice_ids_to_test:
            try:
                voice = client.voices.get(voice_id)
                print(f"✅ {voice_name} (ID: {voice_id}) - Available")
                print(f"   Name: {voice.name}")
                print(f"   Category: {getattr(voice, 'category', 'N/A')}")
            except Exception as e:
                print(f"❌ {voice_name} (ID: {voice_id}) - Error: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice details test failed: {str(e)}")
        return False

def test_account_info():
    """Test account information and credits"""
    print("\n💳 Testing Account Information...")
    
    try:
        from elevenlabs.client import ElevenLabs
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ API key required")
            return False
        
        client = ElevenLabs(api_key=api_key)
        
        # Get user info
        user = client.user.get()
        print(f"✅ Account found: {getattr(user, 'email', 'N/A')}")
        
        # Get subscription info if available
        try:
            subscription = client.user.get_subscription()
            print(f"📋 Subscription tier: {getattr(subscription, 'tier', 'N/A')}")
        except:
            print("📋 Subscription info not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Account info test failed: {str(e)}")
        return False

def main():
    """Run all ElevenLabs API tests"""
    print("🚀 ElevenLabs API Test Suite")
    print("=" * 50)
    
    # Test 1: Basic API connection
    basic_success = test_elevenlabs_basic()
    
    if not basic_success:
        print("\n❌ Basic API test failed. Fix API key issues before proceeding.")
        return
    
    # Test 2: Voice details
    test_voice_details()
    
    # Test 3: Account info
    test_account_info()
    
    # Test 4: Voice generation
    generation_success = test_voice_generation()
    
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print(f"✅ API Connection: {'PASS' if basic_success else 'FAIL'}")
    print(f"✅ Voice Generation: {'PASS' if generation_success else 'FAIL'}")
    
    if basic_success and generation_success:
        print("\n🎉 All tests passed! ElevenLabs API is working correctly.")
        print("💡 Your sales agent should now work with audio generation.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        print("💡 Common solutions:")
        print("   1. Verify your ElevenLabs API key")
        print("   2. Check your account has sufficient credits")
        print("   3. Ensure internet connectivity")
        print("   4. Try a different voice ID if voice-specific errors occur")

if __name__ == "__main__":
    main()