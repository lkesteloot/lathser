//
//  DialView.h
//  Lathser
//
//  Created by Kurt Schaefer on 3/21/15.
//  Copyright (c) 2015 Kurt Schaefer. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface DialView : UIView

// An array of positions around the dial represented in radians.  These will be displayed as marks
// around the dial.

@property (nonatomic, strong) NSArray* positionArry;
@property (nonatomic, assign) NSInteger currentPositionIndex;
@property (nonatomic, assign) CGFloat handAngle;

@end
