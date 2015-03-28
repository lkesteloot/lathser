//
//  ThermalSensorView.h
//  Lathser
//
//  Created by Kurt Schaefer on 3/26/15.
//  Copyright (c) 2015 Kurt Schaefer. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface ThermalSensorView : UIView

@property (nonatomic, assign) NSInteger value;

- (void)drawPulseWithDuration:(CGFloat)duration;

@end
