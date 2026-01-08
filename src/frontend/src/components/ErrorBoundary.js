/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React from 'react';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    console.error('🚨 ErrorBoundary caught error:', error);
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('🚨 ErrorBoundary details:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary p-4">
          <Card className="text-center">
            <i className="pi pi-exclamation-triangle text-6xl text-red-500 mb-3"></i>
            <h2>Something went wrong</h2>
            <p className="text-gray-600 mb-3">
              The AI-Augmented Personal Archive encountered an error.
            </p>
            
            <div className="error-details mb-4">
              <details className="text-left">
                <summary className="cursor-pointer text-sm text-gray-500 mb-2">
                  Show error details
                </summary>
                <div className="bg-gray-100 p-3 border-round text-sm">
                  <strong>Error:</strong> {this.state.error && this.state.error.toString()}
                  <br />
                  <strong>Stack:</strong>
                  <pre className="mt-2 text-xs overflow-auto">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              </details>
            </div>
            
            <Button
              label="Reload Application"
              icon="pi pi-refresh"
              onClick={() => window.location.reload()}
              className="p-button-primary"
            />
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;