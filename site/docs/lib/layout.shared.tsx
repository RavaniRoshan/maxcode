import React from 'react';
import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { appName, gitConfig } from './shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <span className="inline-flex items-center gap-2 font-mono font-semibold">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="1 3 10 10"
            shapeRendering="crispEdges"
            className="w-5 h-5 shrink-0"
            role="img"
            aria-label="maxcode mark"
          >
            <rect x="1" y="3" width="10" height="9" fill="#D9DEE5" />
            <rect x="1" y="3" width="10" height="1" fill="#FFFFFF" />
            <rect x="10" y="4" width="1" height="8" fill="#AEB6C2" />
            <rect x="1" y="11" width="10" height="1" fill="#AEB6C2" />
            <rect x="2" y="12" width="2" height="1" fill="#8D99AB" />
            <rect x="8" y="12" width="2" height="1" fill="#8D99AB" />
            <rect x="3" y="5" width="1" height="2" fill="#0A0F1E" />
            <rect x="8" y="5" width="1" height="2" fill="#0A0F1E" />
            <rect x="4" y="8" width="1" height="1" fill="#0A0F1E" />
            <rect x="7" y="8" width="1" height="1" fill="#0A0F1E" />
            <rect x="5" y="9" width="2" height="1" fill="#0A0F1E" />
          </svg>
          <span>{appName}</span>
        </span>
      ),
    },
    githubUrl: `https://github.com/${gitConfig.user}/${gitConfig.repo}`,
  };
}
