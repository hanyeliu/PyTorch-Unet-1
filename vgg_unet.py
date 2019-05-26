import torch
import torch.nn as nn
from torchvision import models


def double_conv(in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True)
    )


def up_conv(in_channels, out_channels):
    return nn.ConvTranspose2d(
        in_channels, out_channels, kernel_size=2, stride=2
    )


class VGGUnet(nn.Module):
    """Unet with VGG-13 (with BN) encoder.
    """

    def __init__(self, out_channels=2, pretrained=False):
        super().__init__()

        self.encoder = models.vgg13_bn(pretrained=pretrained).features
        self.block1 = nn.Sequential(*self.encoder[:6])
        self.block2 = nn.Sequential(*self.encoder[6:13])
        self.block3 = nn.Sequential(*self.encoder[13:20])
        self.block4 = nn.Sequential(*self.encoder[20:27])
        self.block5 = nn.Sequential(*self.encoder[27:34])

        # compared with Unet, we only modify the first up_conv.
        # up_conv(?, 512), "?" is the #out_channels in block5
        self.up_conv6 = up_conv(512, 512)
        self.conv6 = double_conv(1024, 512)
        self.up_conv7 = up_conv(512, 256)
        self.conv7 = double_conv(512, 256)
        self.up_conv8 = up_conv(256, 128)
        self.conv8 = double_conv(256, 128)
        self.up_conv9 = up_conv(128, 64)
        self.conv9 = double_conv(128, 64)
        self.conv10 = nn.Conv2d(64, out_channels, kernel_size=1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        block1 = self.block1(x)
        block2 = self.block2(block1)
        block3 = self.block3(block2)
        block4 = self.block4(block3)
        block5 = self.block5(block4)

        x = self.up_conv6(block5)
        x = torch.cat([x, block4], dim=1)
        x = self.conv6(x)

        x = self.up_conv7(x)
        x = torch.cat([x, block3], dim=1)
        x = self.conv7(x)

        x = self.up_conv8(x)
        x = torch.cat([x, block2], dim=1)
        x = self.conv8(x)

        x = self.up_conv9(x)
        x = torch.cat([x, block1], dim=1)
        x = self.conv9(x)

        x = self.conv10(x)
        x = self.sigmoid(x)

        return x
