# External ATC Layer

This feature provides an integration layer between Aerofly and external ATC services, specifically designed to work with SayIntentionAI's API. The goal is to enable realistic ATC communication in Aerofly using AI-powered controllers.

## Overview

The external ATC layer acts as a bridge between:
- Aerofly's flight simulator
- SayIntentionAI's ATC API
- Our local ATC state management system

## Components

1. **API Integration**
   - SayIntentionAI API client
   - Authentication and session management
   - Request/response handling

2. **State Translation**
   - Convert Aerofly aircraft state to API format
   - Convert API responses to Aerofly-compatible format
   - Handle state synchronization

3. **Communication Bridge**
   - UDP message handling
   - Protocol translation
   - Error handling and recovery

## Development Status

🚧 **Under Development** 🚧

This is an experimental feature. Current focus:
- [ ] Basic API integration
- [ ] State translation layer
- [ ] Communication protocol
- [ ] Error handling
- [ ] Testing with Aerofly

## Usage

*Coming soon as the feature develops*

## Requirements

- Python 3.8+
- SayIntentionAI API access
- Aerofly with UDP data output enabled

## Configuration

*Configuration details will be added as the feature develops*

## Contributing

Feel free to contribute to this feature by:
1. Testing the integration
2. Reporting issues
3. Suggesting improvements
4. Adding documentation

## License

Same as the main project - open source and free to use. 