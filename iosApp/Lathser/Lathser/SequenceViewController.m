//
//  SequenceViewController.m
//  Lathser
//
//  Created by Kurt Schaefer on 4/13/14.
//  Copyright (c) 2014 Kurt Schaefer.
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

#import "UARTPeripheral.h"
#import "SequenceViewController.h"
#import "LSPeripheralSequencer.h"
#import "DialView.h"
#import "ThermalSensorView.h"
#import "LSNotifcationCenter.h"

@interface SequenceViewController () <LSPeripheralSequencerDelegate>
@property (nonatomic, strong) LSPeripheralSequencer *peripheralSequencer;

@property (weak, nonatomic) IBOutlet UIButton *connectionButton;
@property (weak, nonatomic) IBOutlet UILabel *connectionStatusLabel;

@property (weak, nonatomic) IBOutlet UILabel *sequenceNameLabel;
@property (weak, nonatomic) IBOutlet UILabel *currentStepLabel;
@property (weak, nonatomic) IBOutlet UILabel *totalStepsLabel;
@property (weak, nonatomic) IBOutlet UIProgressView *progressView;

@property (nonatomic, strong) IBOutlet DialView* dialView;
@property (nonatomic, strong) IBOutlet ThermalSensorView* thermalSensorView;

@property (nonatomic, strong) NSMutableArray* positions;
@property (nonatomic, strong) NSString *sequenceName;

@end

@implementation SequenceViewController


- (id)initWithCoder:(NSCoder *)aDecoder
{
    self = [super initWithCoder:aDecoder];
    if (self) {
        self.peripheralSequencer = [[LSPeripheralSequencer alloc] init];
        self.peripheralSequencer.delegate = self;

        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(sequenceURLNotification:) name:kSequenceUrlNotification object:nil];

        self.positions = [[NSMutableArray alloc] init];

        // Temp hard coded sequence for knight.
        [self.positions addObjectsFromArray:
         @[@0,
           @0.392699,
           @0.785398,
           @1.1781,
           @1.5708,
           @1.9635,
           @2.35619,
           @2.74889,
           @0,
           @0.392699,
           @0.785398,
           @1.1781,
           @1.5708,
           @1.9635,
           @2.35619,
           @2.74889,
           @0,
           @0.392699,
           @0.785398,
           @1.1781,
           @1.5708,
           @1.9635,
           @2.35619,
           @2.74889]];
        self.sequenceName = @"Default";
    }

    return self;
}

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.dialView.positionArry = self.positions;
    self.dialView.currentPositionIndex = 0;
}

- (IBAction)connectButtonTouchUpInside:(id)sender
{
    if (self.peripheralSequencer.connectionState == LSPeripheralConnectionStateNotConnected) {
        [self.peripheralSequencer scanForPeripherals];
    } else if (self.peripheralSequencer.connectionState == LSPeripheralConnectionStateScanning ||
               self.peripheralSequencer.connectionState == LSPeripheralConnectionStateConnected) {
        [self.peripheralSequencer disconnect];
    }
}


- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
    // Dispose of any resources that can be recreated.
}

- (void)viewWillAppear:(BOOL)animated
{
    [super viewWillAppear:animated];
    [self  updateProgressBarAndLabels];
}

- (NSInteger)stepValueForRadians:(CGFloat)theta
{
    // For now we assume 32 micro stepping and 400 steps per rev.  So Pi is 200*32
    return floor((theta/M_PI)*(32*200));
}

- (void)sendAndStartCurrentSequence
{
    // Quit whatever we were doing.
    NSMutableArray *stringArray = [[NSMutableArray alloc] init];

    // Quit whatever it was doing.
    [stringArray addObject:@"q"];

    // Kill off any existing sequence values.
    [stringArray addObject:@"x"];

    // Do an "a800 " style adding of each of the coordinates.
    // The positions are sent in steps.
    for (NSNumber* number in self.positions) {
        [stringArray addObject:[NSString stringWithFormat:@"a%ld ", (long)[self stepValueForRadians:[number floatValue]]]];
    }

    // start the sequence, moving to the first location and
    // waiting for the thermal sensor.
    [stringArray addObject:@"s"];

    self.sequenceNameLabel.text = @"Sending...";
    self.progressView.progress = 0;

    __weak typeof(self) weakSelf = self;
    [self.peripheralSequencer sendStringArray:stringArray
                                      success:^(NSString *responce) {
                                          // Send should do a better job of indicating that things need to be sent/have been sent.
                                          weakSelf.dialView.currentPositionIndex = 0;
                                          [weakSelf updateProgressBarAndLabels];
                                          weakSelf.sequenceNameLabel.text = self.sequenceName;
                                      } failure:^(NSString *error) {
                                          weakSelf.sequenceNameLabel.text = @"Send failed";
                                          // TODO: Indicate Error.
                                      } finally:nil];
}

- (IBAction)sendSequenceButtonTouchUpinside:(id)sender
{
    // 7 1/16 steps plus a 9/16 step at the end.
    [self sendAndStartCurrentSequence];
}

- (IBAction)previousButtonTouchUpInside:(id)sender
{
    // It would be nice to have a "heading to"
    // indication that comes up right away, but for now just for preview
    // we let you step through things when not connected.
    if (self.peripheralSequencer.connectionState != LSPeripheralConnectionStateConnected &&
        self.dialView.currentPositionIndex > 0) {
        self.dialView.currentPositionIndex--;
        [self updateProgressBarAndLabels];
    }
    [self.peripheralSequencer sendString:@"p" success:nil failure:nil finally:nil];
}

- (IBAction)nextButtonTouchUpInside:(id)sender
{
    // It would be nice to have a "heading to"
    // indication that comes up right away.
    if (self.peripheralSequencer.connectionState != LSPeripheralConnectionStateConnected &&
        self.dialView.currentPositionIndex + 1 < self.positions.count) {
        self.dialView.currentPositionIndex++;
        [self updateProgressBarAndLabels];
    }
    [self.peripheralSequencer sendString:@"n" success:nil failure:nil finally:nil];
}

- (void)updateConnectionStateLabel
{
    if (self.peripheralSequencer.connectionState == LSPeripheralConnectionStateConnected) {
        self.connectionStatusLabel.text = @"Connected";
    } else if (self.peripheralSequencer.connectionState == LSPeripheralConnectionStateScanning) {
        self.connectionStatusLabel.text = @"Scanning";
    } else if (self.peripheralSequencer.connectionState == LSPeripheralConnectionStateNotConnected) {
        self.connectionStatusLabel.text = @"Not Connected";
    } else {
        NSAssert(FALSE, @"Unknown connection state: %d", (int)self.peripheralSequencer.connectionState);
    }
}

- (void)updateConnectButton
{
    if (self.peripheralSequencer.connectionState == LSPeripheralConnectionStateConnected) {
        [self.connectionButton setTitle:@"Disconnect" forState:UIControlStateNormal];
    } else if (self.peripheralSequencer.connectionState == LSPeripheralConnectionStateScanning) {
        [self.connectionButton setTitle:@"Cancel" forState:UIControlStateNormal];
    } else if (self.peripheralSequencer.connectionState == LSPeripheralConnectionStateNotConnected) {
        [self.connectionButton setTitle:@"Connect" forState:UIControlStateNormal];
    } else {
        NSAssert(FALSE, @"Unknown connection state: %d", (int)self.peripheralSequencer.connectionState);
    }
}

- (void)updateProgressBarAndLabels
{
    NSInteger index = self.dialView.currentPositionIndex;
    [self.progressView setProgress:(float)index/(float)(self.positions.count - 1) animated:YES];
    self.currentStepLabel.text = [NSString stringWithFormat:@"%ld", index + 1];
    self.totalStepsLabel.text = [NSString stringWithFormat:@"%ld", self.positions.count];
}

- (NSString*)hexRepresentationOfData:(NSData*)data withSpaces:(BOOL)spaces
{

    const unsigned char* bytes = (const unsigned char*)[data bytes];
    NSUInteger nbBytes = [data length];

    //If spaces is true, insert a space every this many input bytes (twice this many output characters).
    static const NSUInteger spaceEveryThisManyBytes = 4UL;

    NSUInteger strLen = 2*nbBytes + (spaces ? nbBytes/spaceEveryThisManyBytes : 0);

    NSMutableString* hex = [[NSMutableString alloc] initWithCapacity:strLen];
    for(NSUInteger i=0; i<nbBytes; ) {
        [hex appendFormat:@"0x%x", bytes[i]];
        //We need to increment here so that the every-n-bytes computations are right.
        ++i;

        if (spaces) {
            [hex appendString:@" "];
        }
    }

    return hex;
}

- (void)sequenceURLNotification:(NSNotification*)notification
{
    NSURL *url = [notification object];
    NSURLComponents* urlComponents = [NSURLComponents componentsWithURL:url resolvingAgainstBaseURL:NO];
    NSArray *queryItems = urlComponents.queryItems;

    NSMutableArray* positions = [[NSMutableArray alloc] init];

    for (NSURLQueryItem *item in queryItems) {
        if ([item.name isEqualToString:@"name"]) {
            self.sequenceName = [item.value stringByReplacingPercentEscapesUsingEncoding:NSUTF8StringEncoding];
        } else if (!item.value) {
            // All the point values have empty names.
            [positions addObject:[NSNumber numberWithFloat:[item.name floatValue]]];
        }
    }

    if (positions.count > 0) {
        self.positions = positions;
        self.dialView.positionArry = positions;
        self.sequenceNameLabel.text = self.sequenceName;
        [self sendAndStartCurrentSequence];
    }
}

#pragma mark LSPeripheralSequencerDelegate
- (void)didRecieveString:(NSString*)string
{
    NSArray* stringComponents = [string componentsSeparatedByString:@" "];

    if (stringComponents.count == 1) {
        NSString* command = [stringComponents objectAtIndex:0];
        if ([command isEqualToString:@"THERM"]) {
            [self.thermalSensorView drawPulseWithDuration:0.3];
        }
    } else if (stringComponents.count == 2) {
        NSString* command = [stringComponents objectAtIndex:0];
        NSString* arg = [stringComponents objectAtIndex:1];
        if ([command isEqualToString:@"TEMP"]) {
            self.thermalSensorView.value = [arg integerValue];
        } else if ([command isEqualToString:@"RUN"]) {
            NSInteger newIndex = [arg integerValue];
            if (newIndex >= 0 && newIndex < self.positions.count) {
                self.dialView.currentPositionIndex = [arg integerValue];
                [self updateProgressBarAndLabels];
            }
        } else if ([command isEqualToString:@"POS"]) {
            // Not sure what to do about it saying exactly where it is.
            // We should probably do something about this, but for now
            // since we're not doing direct remote controlling we do everything by index.
            // Knowing the current position will allow us to estiamate animation times better.
        }
    }
}

- (void)connectionStateChanged:(LSPeripheralConnectionState)connectionState
{
    [self updateConnectionStateLabel];
    [self updateConnectButton];

    // We put this to white if we're disconnected so we don't show a misleading
    // green light.
    if (connectionState != LSPeripheralConnectionStateConnected) {
        self.thermalSensorView.value = 1;
    }
}


@end
