//
//  ThermalSensorView.m
//  Lathser
//
//  Created by Kurt Schaefer on 3/26/15.
//  Copyright (c) 2015 Kurt Schaefer. All rights reserved.
//

#import "ThermalSensorView.h"

@interface ThermalSensorView ()

@property (nonatomic, strong) UIView* thermalSensorBackgroundView;
@property (nonatomic, strong) UIImageView* thermalSensorImageView;
@property (nonatomic, strong) CAShapeLayer *shapeLayer;

@end

@implementation ThermalSensorView

- (id)initWithCoder:(NSCoder *)aDecoder
{
    self = [super initWithCoder:aDecoder];
    if (self) {
        [self commonInit];
    }
    return self;
}

- (void)commonInit
{
    _thermalSensorImageView = [[UIImageView alloc] initWithImage:[UIImage imageNamed:@"thermalSensor51x44"]];
    _thermalSensorBackgroundView = [[UIView alloc] initWithFrame:self.bounds];

    _shapeLayer = [[CAShapeLayer alloc] init];

    [self addSubview:self.thermalSensorBackgroundView];
    [self addSubview:self.thermalSensorImageView];

    self.backgroundColor = [UIColor clearColor];
}

- (void)layoutSubviews
{
    [super layoutSubviews];
    self.thermalSensorImageView.frame = self.bounds;
    CGFloat border = floor(self.bounds.size.width/6.0f);
    self.thermalSensorBackgroundView.frame = CGRectInset(self.bounds, border, border);
}

- (UIColor *)interpColorFrom:(UIColor*)fromColor
                          to:(UIColor *)toColor
                           t:(float)t
{
    if (t < 0.0f) {
        return fromColor;
    }
    if (t > 1.0f) {
        return toColor;
    }

    const CGFloat *fromComponents = CGColorGetComponents(fromColor.CGColor);
    const CGFloat *toComponents = CGColorGetComponents(toColor.CGColor);

    float r = fromComponents[0] + (toComponents[0] - fromComponents[0])*t;
    float g = fromComponents[1] + (toComponents[1] - fromComponents[1])*t;
    float b = fromComponents[2] + (toComponents[2] - fromComponents[2])*t;

    return [UIColor colorWithRed:r green:g blue:b alpha:1.0];
}

- (void)setValue:(NSInteger)value
{
    _value = value;

    // Zero indicates not connected. For now we show white, but really we should
    // have an icon or a tiny "NC" or something.
    if (value == 0) {
        self.thermalSensorBackgroundView.backgroundColor = [UIColor whiteColor];
        return;
    }

    if (value == -1) {
    }

    UIColor* bottomColor = [UIColor colorWithRed:93.0/255.0
                                           green:157.0/255.0
                                            blue:73.0/255.0 alpha:1.0];
    UIColor* middleColor = [UIColor colorWithRed:219.0/255.0
                                           green:217.0/255.0
                                            blue:74.0/255.0 alpha:1.0];
    UIColor* topColor = [UIColor colorWithRed:218.0/255.0
                                        green:78.0/255.0
                                         blue:68.0/255.0 alpha:1.0];

    CGFloat ratio = (CGFloat)value/1024.0f;
    UIColor* color = bottomColor;

    if (ratio < 0.5) {
        color = [self interpColorFrom:bottomColor to:middleColor t:ratio*2.0];
    } else {
        color = [self interpColorFrom:middleColor to:topColor t:ratio*2.0 - 1.0];
    }
    self.thermalSensorBackgroundView.backgroundColor = color;
}

- (UIBezierPath *)bezierPathForCircleWithRadius:(CGFloat)radius alpha:(CGFloat)alpha lineWidth:(CGFloat)lineWidth
{
    return [UIBezierPath bezierPathWithRoundedRect:
            CGRectMake(CGRectGetMidX(self.bounds) - radius,
                       CGRectGetMidX(self.bounds) - radius, 2.0*radius, 2.0*radius) cornerRadius:radius];
}

- (void)drawPulseWithDuration:(CGFloat)duration
{

    [self.layer insertSublayer:self.shapeLayer above:self.thermalSensorImageView.layer];

    self.shapeLayer.fillColor = nil;
    self.shapeLayer.strokeColor = [UIColor colorWithRed:1.0 green:0.0 blue:0.0 alpha:1.0].CGColor;
    self.shapeLayer.lineWidth = 2.0;

    CGFloat MinCircleRadius = 11.0f;
    CGFloat MaxCircleRadius = 17.0f;
    CGFloat CircleLineWidth = 3.0;

    CFTimeInterval startTime = CACurrentMediaTime();

    CGFloat startRadius = MinCircleRadius - CircleLineWidth/2.0;
    CGFloat endRadius = MaxCircleRadius - CircleLineWidth/2.0;

    // Horrible offset hack 2.5 remove once we have normalized image for this.
    CGPathRef startPath =  [UIBezierPath bezierPathWithRoundedRect:
                            CGRectMake(CGRectGetMidX(self.bounds) - startRadius,
                                       CGRectGetMidX(self.bounds) - startRadius - 2.5, 2.0*startRadius, 2.0*startRadius) cornerRadius:startRadius].CGPath;

    CGPathRef endPath = [UIBezierPath bezierPathWithRoundedRect:
                         CGRectMake(CGRectGetMidX(self.bounds) - endRadius,
                                    CGRectGetMidX(self.bounds) - endRadius - 2.5, 2.0*endRadius, 2.0*endRadius)
                                                   cornerRadius:endRadius].CGPath;

    CABasicAnimation *circleAnimation = [CABasicAnimation animationWithKeyPath:@"path"];
    circleAnimation.timingFunction = [CAMediaTimingFunction functionWithName:kCAMediaTimingFunctionEaseOut];
    circleAnimation.fromValue = (__bridge id)startPath;
    circleAnimation.toValue = (__bridge id)endPath;
    circleAnimation.beginTime = startTime;
    circleAnimation.duration = duration;
    circleAnimation.fillMode = kCAFillModeForwards;
    circleAnimation.removedOnCompletion = NO;
    [self.shapeLayer addAnimation:circleAnimation forKey:@"circleAnimationKey"];

    CABasicAnimation *circleOpacityAnimation = [CABasicAnimation animationWithKeyPath:@"opacity"];
    circleOpacityAnimation.timingFunction = [CAMediaTimingFunction functionWithName:kCAMediaTimingFunctionEaseOut];
    circleOpacityAnimation.fromValue = [NSNumber numberWithDouble:1.0];
    circleOpacityAnimation.toValue = [NSNumber numberWithDouble:0.0];
    circleOpacityAnimation.beginTime = startTime;
    circleOpacityAnimation.duration = duration;
    circleOpacityAnimation.fillMode = kCAFillModeForwards;
    circleOpacityAnimation.removedOnCompletion = NO;
    [self.shapeLayer addAnimation:circleOpacityAnimation forKey:@"opacityAnimationKey"];
}

@end
