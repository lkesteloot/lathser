//
//  DialView.m
//  Lathser
//
//  Created by Kurt Schaefer on 3/21/15.
//  Copyright (c) 2015 Kurt Schaefer. All rights reserved.
//

#import "DialView.h"

@interface DialView ()
@property (nonatomic, strong) UIImageView* faceImageView;
@property (nonatomic, strong) UIImageView* handImageView;
@property (nonatomic, strong) UIView* dialMarkContainerView;
@property (nonatomic, strong) NSMutableArray* markViews;
@end

@implementation DialView

- (id)initWithCoder:(NSCoder *)aDecoder
{
    self = [super initWithCoder:aDecoder];
    if (self) {
        [self commonInit];
    }
    return self;
}

- (id)initWithFrame:(CGRect)frame
{
    self = [super initWithFrame:frame];
    if (self) {
        [self commonInit];
    }
    return self;
}

- (void)commonInit
{
    self.markViews = [[NSMutableArray alloc] init];

    self.faceImageView = [[UIImageView alloc] initWithImage:[UIImage imageNamed:@"dialFace281x281"]];
    self.faceImageView.frame = self.bounds;
    self.faceImageView.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    self.faceImageView.contentMode = UIViewContentModeScaleAspectFill;
    self.faceImageView.alpha = 0.75;
    self.faceImageView.opaque = FALSE;
    self.backgroundColor = [UIColor clearColor];
    [self addSubview:self.faceImageView];

    self.handImageView = [[UIImageView alloc] initWithImage:[UIImage imageNamed:@"dialHand41x135"]];
    // Compute the anchor point so it's at the proper rotation point
    // for the handle (which in 2x is 135 pixels tall and the center of
    // rotation is 20.5 pixels in.
    self.handImageView.layer.anchorPoint = CGPointMake(0.5, 1.0 - (20.5/135.0));

    // TODO: Rework this so it resizes properly.
    CGFloat padding = floor((self.bounds.size.width - 41)/2.0f);
    CGFloat topPad = floor(self.bounds.size.height/13);

    self.handImageView.frame = CGRectMake(padding, topPad, 41, 135);
    [self addSubview:self.handImageView];

    self.dialMarkContainerView = [[UIView alloc] initWithFrame:self.bounds];
    [self addSubview:self.dialMarkContainerView];
}

- (UIView*)createDialMarkView:(CGFloat)theta
{
    UIImageView* markImageView = [[UIImageView alloc] initWithImage:[UIImage imageNamed:@"dialMark19x46"]];
    markImageView.bounds = CGRectMake(0.0f, 0.0f, 6.0, 14.0);
    markImageView.layer.anchorPoint = CGPointMake(0.5, 0.5);
    UIView* parentView  = [[UIView alloc] initWithFrame:self.bounds];
    parentView.layer.anchorPoint = CGPointMake(0.5f, 0.5f);
    parentView.transform = CGAffineTransformRotate(parentView.transform, theta);
    CGFloat size = self.bounds.size.width;

    markImageView.frame = CGRectMake((size - markImageView.bounds.size.width)/2.0,
                                     7, markImageView.bounds.size.width, markImageView.bounds.size.height);
    [parentView addSubview:markImageView];
    return parentView;
}

- (void)setPositionArry:(NSArray *)positionArry
{
    _positionArry = positionArry;
    NSArray *viewsToRemove = [self.dialMarkContainerView subviews];
    for (UIView *view in viewsToRemove) {
        [view removeFromSuperview];
    }

    [self.markViews removeAllObjects];

    for (NSInteger i=0; i<self.positionArry.count; ++i) {
        NSNumber* theta = [self.positionArry objectAtIndex:i];
        UIView* markView = [self createDialMarkView:[theta floatValue]];
        [self.dialMarkContainerView addSubview:markView];
        [self.markViews addObject:markView];
        [self addSubview:markView];
    }
}

- (void)setCurrentPositionIndex:(NSInteger)currentPositionIndex
{
    _currentPositionIndex = currentPositionIndex;
    NSInteger index = 0;
    for (UIView* view in self.markViews) {
        view.alpha = (index == currentPositionIndex) ? 1.0 : 0.1;
        index++;
    }
    [self setHandAngle:[[self.positionArry objectAtIndex:currentPositionIndex] floatValue]];
}

- (void)rotateImage:(UIImageView *)image duration:(NSTimeInterval)duration
              curve:(int)curve radians:(CGFloat)radians
{
    // Setup the animation
    [UIView beginAnimations:nil context:NULL];
    [UIView setAnimationDuration:duration];
    [UIView setAnimationCurve:curve];
    [UIView setAnimationBeginsFromCurrentState:YES];

    // The transform matrix
    CGAffineTransform transform =
    CGAffineTransformMakeRotation(radians);
    image.transform = transform;

    // Commit the changes
    [UIView commitAnimations];
}

- (void)setHandAngle:(CGFloat)handAngle
{
    if (_handAngle == handAngle) {
        return;
    }
    _handAngle = handAngle;
    [self rotateImage:self.handImageView duration:.3 curve:UIViewAnimationCurveEaseInOut radians:handAngle];
}

@end

