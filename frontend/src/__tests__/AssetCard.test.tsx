// @vitest-environment jsdom  
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AssetCard } from '../components/AssetCard';
import { vi, describe, it, expect } from 'vitest';
import { Asset } from '../types/assets';

describe('AssetCard Component', () => {
  const mockAsset: Asset = {
    id: 99,
    asset_type: 'image',
    file_url: '/api/assets/99/download',
    is_favorite: false,
    is_deleted: false,
    created_at: '2026-06-23T00:00:00Z',
    updated_at: '2026-06-23T00:00:00Z',
    title: 'Test Asset Title'
  };

  it('renders correctly and does not expose file_path', () => {
    const { container } = render(
      <AssetCard
        asset={mockAsset}
        onToggleFavorite={vi.fn()}
        onDelete={vi.fn()}
        onRestore={vi.fn()}
      />
    );

    // Verify title is rendered
    expect(screen.getByText('Test Asset Title')).toBeTruthy();

    // Verify file_path is NOT rendered anywhere in the DOM
    const html = container.innerHTML;
    expect(html).not.toContain('file_path');

    // Verify file_url is used for image source
    const img = screen.getByRole('img');
    expect(img.getAttribute('src')).toBe('/api/assets/99/download');
  });

  it('calls bulk selection toggle when checkbox is clicked', () => {
    const onToggleSelection = vi.fn();
    render(
      <AssetCard
        asset={mockAsset}
        isSelected={false}
        onToggleSelection={onToggleSelection}
        onToggleFavorite={vi.fn()}
        onDelete={vi.fn()}
        onRestore={vi.fn()}
      />
    );

    const checkbox = screen.getByRole('checkbox', { name: /select asset/i });
    fireEvent.click(checkbox);
    expect(onToggleSelection).toHaveBeenCalledWith(99);
  });
});
