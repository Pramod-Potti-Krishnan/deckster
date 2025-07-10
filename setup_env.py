#!/usr/bin/env python3
"""
Quick setup script to help configure the .env file.
"""
import os
import sys


def main():
    print("Deckster Environment Setup")
    print("=" * 50)
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("✓ .env file found")
    else:
        print("Creating .env file from .env.example...")
        os.system('cp .env.example .env')
        print("✓ .env file created")
    
    print("\nYou need to configure at least one AI service to use Deckster.")
    print("\nOptions:")
    print("1. OpenAI API Key")
    print("2. Anthropic API Key")
    print("3. Both (recommended)")
    
    choice = input("\nWhich would you like to configure? (1/2/3): ").strip()
    
    env_updates = []
    
    if choice in ['1', '3']:
        openai_key = input("\nEnter your OpenAI API key (or press Enter to skip): ").strip()
        if openai_key:
            env_updates.append(('OPENAI_API_KEY', openai_key))
    
    if choice in ['2', '3']:
        anthropic_key = input("\nEnter your Anthropic API key (or press Enter to skip): ").strip()
        if anthropic_key:
            env_updates.append(('ANTHROPIC_API_KEY', anthropic_key))
    
    # Optional: Supabase configuration
    print("\nSupabase configuration (optional - press Enter to skip each):")
    supabase_url = input("Supabase URL: ").strip()
    if supabase_url:
        env_updates.append(('SUPABASE_URL', supabase_url))
        
        supabase_anon = input("Supabase Anon Key: ").strip()
        if supabase_anon:
            env_updates.append(('SUPABASE_ANON_KEY', supabase_anon))
    
    # Update .env file
    if env_updates:
        print("\nUpdating .env file...")
        
        # Read current .env
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update values
        updated = False
        for i, line in enumerate(lines):
            for key, value in env_updates:
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    updated = True
                    print(f"✓ Updated {key}")
        
        # Write back
        with open('.env', 'w') as f:
            f.writelines(lines)
        
        print("\n✓ Environment configuration complete!")
        print("\nYou can now run:")
        print("  python main.py")
        print("\nOr test the Director agent:")
        print("  python test/test_director_interactive.py")
    else:
        print("\nNo configuration changes made.")
        print("Please edit .env manually to add your API keys.")


if __name__ == "__main__":
    main()