//
//  DialView.h
//  Lathser
//
//  Created by Kurt Schaefer on 3/21/15.
//  Copyright (c) 2015 Kurt Schaefer.
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.
//
//  DialView:
//     This is a Dial display that shows a sequence of posiitions around the dial
//     and has an indicator arm which points to the currentPositionIndex's position.
//

#import <UIKit/UIKit.h>

@interface DialView : UIView

// An array of positions around the dial represented in radians.  These will be displayed as marks
// around the edge of the dial's face.

@property (nonatomic, strong) NSArray* positionArry;
@property (nonatomic, assign) NSInteger currentPositionIndex;
@property (nonatomic, assign) CGFloat handAngle;

@end
