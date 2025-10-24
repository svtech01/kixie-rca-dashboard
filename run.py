#!/usr/bin/env python3
"""
Main entry point for the Kixie Powerlist RCA Dashboard.
"""

from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5005)

