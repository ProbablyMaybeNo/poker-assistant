
import cv2
import numpy as np
import os
from pathlib import Path

# Config
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "models" / "card_templates"
OUT_DIR = PROJECT_ROOT / "models" / "templates"
RANK_DIR = OUT_DIR / "ranks"
SUIT_DIR = OUT_DIR / "suits"

def ensure_dirs():
    RANK_DIR.mkdir(parents=True, exist_ok=True)
    SUIT_DIR.mkdir(parents=True, exist_ok=True)

def process_templates():
    ensure_dirs()
    
    # Iterate over all pngs
    files = list(RAW_DIR.glob("*.png"))
    print(f"Found {len(files)} raw templates.")
    
    for f in files:
        name = f.stem # e.g. "Ah"
        if len(name) != 2:
            print(f"Skipping {name}: invalid format (needs 2 chars, e.g., 'Ah', 'Td')")
            continue
            
        rank_char = name[0] # 'A'
        suit_char = name[1] # 'h'
        
        # Validate chars
        if rank_char not in "23456789TJQKA":
            print(f"Skipping {name}: invalid rank {rank_char}")
            continue
        if suit_char not in "hdcs":
            print(f"Skipping {name}: invalid suit {suit_char}")
            continue

        img = cv2.imread(str(f))
        if img is None:
            print(f"Error reading {f}")
            continue
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Debug "Ah" specifically
        if name == "Ah":
            print(f"DEBUG Ah: Shape={gray.shape}")
            cv2.imwrite(str(OUT_DIR / "debug_Ah_gray.png"), gray)
        
        # Crop Top-Left Corner Region of Interest (ROI)
        # Increase area key info
        h, w = gray.shape
        roi_w = int(w * 0.55) # Wider
        roi_h = int(h * 1.0) # Full height of left side? No, rank/suit is top ~70% usually.
        # Let's go safe.
        roi_h = int(h * 0.70)
        roi = gray[0:roi_h, 0:roi_w]
        
        # Contrast Enhancement
        roi = cv2.equalizeHist(roi)
        
        if name == "Ah":
             # Pixel stats
             print(f"DEBUG Ah: ROI stats - Min={np.min(roi)}, Max={np.max(roi)}, Mean={np.mean(roi):.2f}")
             cv2.imwrite(str(OUT_DIR / "debug_Ah_roi.png"), roi)

        # Threshold: Use Otsu's Binarization
        # This automatically finds the best threshold value.
        _, thresh = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        if name == "Ah":
             cv2.imwrite(str(OUT_DIR / "debug_Ah_thresh.png"), thresh)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if name == "Ah":
            print(f"DEBUG Ah: Found {len(contours)} contours")
        
        # We expect at least 2 significant contours: Rank (top) and Suit (bottom).
        # Filter small noise.
        valid_contours = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            if cw * ch > 30: # Lowered min area slightly
                valid_contours.append((x, y, cw, ch))
                
        # Sort by Y position (Rank is above Suit)
        valid_contours.sort(key=lambda c: c[1])
        
        if len(valid_contours) < 2:
            print(f"Warning: {name} - Found {len(valid_contours)} contours (expected >=2). Using fallback crop.")
            # Fallback to fixed split if detection fails
            rank_h = int(roi_h * 0.55)
            # Ensure ROI is valid
            if rank_h > 0 and roi.shape[1] > 0:
                rank_img = roi[0:rank_h, :]
                suit_img = roi[rank_h:, :]
            else:
                 print(f"Error: ROI too small for {name}")
                 continue
        else:
            # Rank is the top-most significant contour (or group of contours if '10')
            # Suit is the contour below it.
            
            # Special case for '10': The rank is '1' and '0'. They might be separate contours.
            # If standard ranks are single chars, '10' might be two side-by-side.
            
            # Let's take the top-most extraction as Rank.
            # If we have > 2 contours, we need to group the top ones for rank?
            
            # Heuristic: Check the first two contours. If they are horizontally adjacent (similar Y, close X), they are "10".
            # The suit is usually strictly below.
            
            c1 = valid_contours[0]
            c2 = valid_contours[1]
            
            # Check Y-overlap or proximity
            # c = (x, y, w, h)
            # If c2.y is close to c1.y (within 50% of height), it's part of the rank (Rank 10)
            
            rank_rects = [c1]
            suit_rect = c2
            
            if abs(c1[1] - c2[1]) < (c1[3] * 0.5):
                # c2 is part of rank (10)
                rank_rects.append(c2)
                if len(valid_contours) > 2:
                    suit_rect = valid_contours[2]
                else:
                    # Missing suit?
                    print(f"Warning: {name} - Likely '10' but missing suit contour. Using fallback.")
                    rank_h = int(roi_h * 0.55)
                    rank_img = roi[0:rank_h, :]
                    suit_img = roi[rank_h:, :]
                    
                    # Save and continue
                    cw_path = RANK_DIR / f"{rank_char}.png"
                    cv2.imwrite(str(cw_path), rank_img)
                    continue

            # Merge rank rects
            min_x = min([r[0] for r in rank_rects])
            min_y = min([r[1] for r in rank_rects])
            max_x = max([r[0] + r[2] for r in rank_rects])
            max_y = max([r[1] + r[3] for r in rank_rects])
            
            # Add padding
            pad = 2
            h_img, w_img = roi.shape
            r_y1 = max(0, min_y - pad)
            r_y2 = min(h_img, max_y + pad)
            r_x1 = max(0, min_x - pad)
            r_x2 = min(w_img, max_x + pad)
            
            rank_img = roi[r_y1:r_y2, r_x1:r_x2]
            
            # Suit rect
            sx, sy, sw, sh = suit_rect
            s_y1 = max(0, sy - pad)
            s_y2 = min(h_img, sy + sh + pad)
            s_x1 = max(0, sx - pad)
            s_x2 = min(w_img, sx + sw + pad)
            
            suit_img = roi[s_y1:s_y2, s_x1:s_x2]

        # Save
        rank_path = RANK_DIR / f"{rank_char}.png"
        suit_path = SUIT_DIR / f"{suit_char}.png"
        
        # Only save if not exists or overwrite?
        # Let's overwrite to ensure latest version
        cv2.imwrite(str(rank_path), rank_img)
        cv2.imwrite(str(suit_path), suit_img)
        
        print(f"Processed {name} -> Rank: {rank_char}, Suit: {suit_char}")

if __name__ == "__main__":
    process_templates()
