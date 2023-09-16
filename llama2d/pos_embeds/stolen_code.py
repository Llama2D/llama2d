import torch
from typing import Any, Optional, Tuple

import numpy as np
import torch.nn as nn

from ..constants import SCREEN_RESOLUTION

class PositionEmbeddingRandom(nn.Module):
    """
    Positional encoding using random spatial frequencies.
    """

    def __init__(self, num_pos_feats: int = 64, scale: Optional[float] = None) -> None:
        super().__init__()
        if scale is None or scale <= 0.0:
            scale = 1.0
        self.register_buffer(
            "positional_encoding_gaussian_matrix",
            scale * torch.randn((2, num_pos_feats)),
        )

        # 0 is for not a point, 1 is for a point
        self.is_a_point_embed = nn.Embedding(2, num_pos_feats)

    def _pe_encoding(self, coords: torch.Tensor) -> torch.Tensor:
        """Positionally encode points that are normalized to [0,1]."""
        # assuming coords are in [0, 1]^2 square and have d_1 x ... x d_n x 2 shape
        coords = 2 * coords - 1
        coords = coords @ self.positional_encoding_gaussian_matrix
        coords = 2 * np.pi * coords
        # outputs d_1 x ... x d_n x C shape
        return torch.cat([torch.sin(coords), torch.cos(coords)], dim=-1)

    def forward(self, size: Tuple[int, int]) -> torch.Tensor:
        """Generate positional encoding for a grid of the specified size."""
        h, w = size
        device: Any = self.positional_encoding_gaussian_matrix.device
        grid = torch.ones((h, w), device=device, dtype=torch.float32)
        y_embed = grid.cumsum(dim=0) - 0.5
        x_embed = grid.cumsum(dim=1) - 0.5
        y_embed = y_embed / h
        x_embed = x_embed / w

        pe = self._pe_encoding(torch.stack([x_embed, y_embed], dim=-1))
        return pe.permute(2, 0, 1)  # C x H x W

    def forward_with_coords(
        self, coords_input: torch.Tensor, image_size: Tuple[int, int]
    ) -> torch.Tensor:
        """Positionally encode points that are not normalized to [0,1]."""
        coords = coords_input.clone()
        coords[:, :, 0] = coords[:, :, 0] / image_size[1]
        coords[:, :, 1] = coords[:, :, 1] / image_size[0]
        return self._pe_encoding(coords.to(torch.float))  # B x N x C


    def apply_rotary_2d_pos_emb(self,q,k,coords):
        # shape of q and k: [bs, ???, seq_len, dim]
        # aka: B x ??? x N x C
        # shape of coords: [bs, ???, seq_len, 2]

        # maybe ??? is 1:
        assert q.shape[1] == 1,f"The ??? dimension of q is {q.shape[1]}, not 1"
        assert k.shape[1] == 1,f"The ??? dimension of k is {k.shape[1]}, not 1"
        assert len(coords.shape) == 4,f"The shape of coords should have dims (bs,???,seq_len,2)"
        assert coords.shape[1] == 1,f"The ??? dimension of coords is {coords.shape[1]}, not 1"

        bs,_,seq_len,dim = q.shape

        # some coords will be [-1,-1] because they have no known position
        # we should not add these coords to the positional embedding
        is_a_point = coords[:,:,0] != -1

        pos_embeds = self.forward_with_coords(coords.squeeze(1),image_size=SCREEN_RESOLUTION)
        assert pos_embeds.shape == (bs,seq_len,dim)

        is_a_point_embeds = self.is_a_point_embed(is_a_point.long())
        assert is_a_point_embeds.shape == (bs,seq_len,dim)

        # add the positional embedding to the query and key
        q = q + pos_embeds.unsqueeze(1)
        k = k + pos_embeds.unsqueeze(1)

        return q,k,is_a_point_embeds