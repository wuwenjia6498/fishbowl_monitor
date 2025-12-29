'use client';

import React from 'react';

/**
 * Footer 组件
 * 页面底部版权信息
 */
export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-background border-t mt-auto">
      <div className="container mx-auto px-4 py-6">
        <div className="text-center text-sm text-muted-foreground">
          <p>© {currentYear} 鱼盆趋势雷达 Fishbowl Monitor. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
