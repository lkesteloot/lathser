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
#import "DialView.h"
#import "ThermalSensorView.h"

typedef NS_ENUM(NSInteger, JogConnectionState) {
    JogConnectionStateNotConnected = 0,
    JogConnectionStateScanning,
    JogConnectionStateConnected,
};


@interface SequenceViewController ()
@property (nonatomic, strong) CBCentralManager *cbManager;

@property (weak, nonatomic) IBOutlet UIButton *connectionButton;
@property (weak, nonatomic) IBOutlet UILabel *connectionStatusLabel;

@property (nonatomic, strong) UARTPeripheral* currentPeripheral;
@property (nonatomic, assign) JogConnectionState connectionState;

@property (nonatomic, strong) IBOutlet DialView* dialView;
@property (nonatomic, strong) IBOutlet ThermalSensorView* thermalSensorView;

@property (nonatomic, strong) NSMutableArray* positions;

@end

@implementation SequenceViewController


- (id)initWithCoder:(NSCoder *)aDecoder
{
    self = [super initWithCoder:aDecoder];
    if (self) {
        self.cbManager = [[CBCentralManager alloc] initWithDelegate:self queue:nil];
        self.connectionState = JogConnectionStateNotConnected;

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
    if (self.connectionState == JogConnectionStateNotConnected) {
        [self scanForPeripherals];
    } else if (self.connectionState == JogConnectionStateScanning ||
               self.connectionState == JogConnectionStateConnected) {
        self.connectionState = JogConnectionStateNotConnected;
        if (self.currentPeripheral.peripheral) {
            [self.cbManager cancelPeripheralConnection:self.currentPeripheral.peripheral];
        }
    }
}

- (void)scanForPeripherals
{
    // skip scanning if UART is already connected
    NSArray *connectedPeripherals = [self.cbManager retrieveConnectedPeripheralsWithServices:@[UARTPeripheral.uartServiceUUID]];
    if ([connectedPeripherals count] > 0) {
        [self connectPeripheral:[connectedPeripherals objectAtIndex:0]];
    } else {
        self.connectionState = JogConnectionStateScanning;
        [self.cbManager scanForPeripheralsWithServices:@[UARTPeripheral.uartServiceUUID]
                                               options:@{CBCentralManagerScanOptionAllowDuplicatesKey: [NSNumber numberWithBool:FALSE]}];
    }
}

- (void)connectPeripheral:(CBPeripheral*)peripheral
{
    // Clear off any pending connections
    [self.cbManager cancelPeripheralConnection:peripheral];

    // Connect
    self.currentPeripheral = [[UARTPeripheral alloc] initWithPeripheral:peripheral delegate:self];
    [self.cbManager connectPeripheral:peripheral options:@{CBConnectPeripheralOptionNotifyOnDisconnectionKey: [NSNumber numberWithBool:TRUE]}];
}

- (void)disconnect
{
    self.connectionState = JogConnectionStateNotConnected;
    [self.cbManager cancelPeripheralConnection:self.currentPeripheral.peripheral];
}

- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
    // Dispose of any resources that can be recreated.
}

- (NSInteger)stepValueForRadians:(CGFloat)theta
{
    // For now we assume 32 micro stepping and 400 steps per rev.  So Pi is 200*32
    return floor((theta/M_PI)*(32*200));
}

- (void)sendAndStartCurrentSequence
{
    // Quit whatever we were doing.
    [self sendString:@"q"];

    // Do an "a800 " style adding of each of the coordinates.
    // The positions are sent in steps.
    for (NSNumber* number in self.positions) {
        [self sendString:[NSString stringWithFormat:@"a%ld ", (long)[self stepValueForRadians:[number floatValue]]]];
    }

    // start the sequence, moving to the first location and
    // waiting for the thermal sensor.
    [self sendString:@"s"];
}

- (IBAction)sendSequenceButtonTouchUpinside:(id)sender
{
    // 7 1/16 steps plus a 9/16 step at the end.
    [self sendAndStartCurrentSequence];
}

- (IBAction)previousButtonTouchUpInside:(id)sender
{
    // It would be nice to have a "heading to"
    // indication that comes up right away.
//    if (self.dialView.currentPositionIndex > 0) {
//        self.dialView.currentPositionIndex--;
//    }
    [self sendString:@"p"];
}

- (IBAction)nextButtonTouchUpInside:(id)sender
{
    // It would be nice to have a "heading to"
    // indication that comes up right away.
//    if (self.dialView.currentPositionIndex + 1 < self.positions.count) {
//        self.dialView.currentPositionIndex++;
//    }
    [self sendString:@"n"];
}

- (void)updateConnectionStateLabel
{
    if (self.connectionState == JogConnectionStateConnected) {
        self.connectionStatusLabel.text = @"Connected";
    } else if (self.connectionState == JogConnectionStateScanning) {
        self.connectionStatusLabel.text = @"Scanning";
    } else if (self.connectionState == JogConnectionStateNotConnected) {
        self.connectionStatusLabel.text = @"Not Connected";
    } else {
        NSAssert(FALSE, @"Unknown connection state: %d", (int)self.connectionState);
    }
}

- (void)updateConnectButton
{
    if (self.connectionState == JogConnectionStateConnected) {
        [self.connectionButton setTitle:@"Disconnect" forState:UIControlStateNormal];
    } else if (self.connectionState == JogConnectionStateScanning) {
        [self.connectionButton setTitle:@"Cancel" forState:UIControlStateNormal];
    } else if (self.connectionState == JogConnectionStateNotConnected) {
        [self.connectionButton setTitle:@"Connect" forState:UIControlStateNormal];
    } else {
        NSAssert(FALSE, @"Unknown connection state: %d", (int)self.connectionState);
    }
}

- (void)setConnectionState:(JogConnectionState)connectionState
{
    if (_connectionState == connectionState) {
        return;
    }
    _connectionState = connectionState;
    [self updateConnectionStateLabel];
    [self updateConnectButton];

    // We put this to white if we're disconnected so we don't show a misleading
    // green light.
    if (self.connectionState != JogConnectionStateConnected) {
        self.thermalSensorView.value = 1;
    }
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

- (void)sendString:(NSString*)string
{
    NSLog(@"SendString: \"%@\"", string);
    NSData *data = [NSData dataWithBytes:string.UTF8String length:string.length];
    [self sendData:data];
}

- (void)sendData:(NSData*)data
{
    // Output data to UART peripheral
    NSString *hexString = [self hexRepresentationOfData:data withSpaces:YES];
    NSLog(@"Sending: %@", hexString);

    [self.currentPeripheral writeRawData:data];
}


- (void)clearPositonArray
{
    [self sendString:@"x"];
}

- (void)addPosition:(NSInteger)position
{
    [self sendString:[NSString stringWithFormat:@"a%@ ", @(position)]];
}

- (void)startSequence
{
    [self sendString:@"s"];
}


#pragma mark CBCentralManagerDelegate
- (void)centralManagerDidUpdateState:(CBCentralManager*)central
{
    NSLog(@"centralManagerDidUpdateState");
    switch (central.state) {
        case CBCentralManagerStatePoweredOff:
            NSLog(@"CoreBluetooth BLE hardware is powered off");
            break;
        case CBCentralManagerStatePoweredOn:
            NSLog(@"CoreBluetooth BLE hardware is powered on and ready");
            break;
        case CBCentralManagerStateResetting:
            NSLog(@"CoreBluetooth BLE hardware is resetting");
            break;
        case CBCentralManagerStateUnauthorized:
            NSLog(@"CoreBluetooth BLE state is unauthorized");
            break;
        case CBCentralManagerStateUnknown:
            NSLog(@"CoreBluetooth BLE state is unknown");
            break;
        case CBCentralManagerStateUnsupported:
            NSLog(@"CoreBluetooth BLE hardware is unsupported on this platform");
            break;
        default:
            break;
    }
}

- (void)centralManager:(CBCentralManager *)central didDiscoverPeripheral:(CBPeripheral *)peripheral advertisementData:(NSDictionary *)advertisementData RSSI:(NSNumber *)RSSI
{
    NSLog(@"Did discover peripheral %@", peripheral.name);
    NSLog(@"With data: %@", advertisementData);
    [self.cbManager stopScan];
    [self connectPeripheral:peripheral];
}

- (void)centralManager:(CBCentralManager*)central didConnectPeripheral:(CBPeripheral*)peripheral
{
    NSLog(@"didConnectPeripheral: %@", peripheral);
    if ([self.currentPeripheral.peripheral isEqual:peripheral]) {
        // already discovered services, DO NOT re-discover. Just pass along the peripheral.
        if (peripheral.services){
            NSLog(@"Did connect to existing peripheral %@", peripheral.name);
            [self.currentPeripheral peripheral:peripheral didDiscoverServices:nil];
        } else {
            NSLog(@"Did connect peripheral %@", peripheral.name);
            [self.currentPeripheral didConnect];
        }
    }
}

- (void) centralManager:(CBCentralManager*)central
didDisconnectPeripheral:(CBPeripheral*)peripheral
                  error:(NSError*)error
{
    NSLog(@"Did disconnect peripheral %@", peripheral.name);
    [self peripheralDidDisconnect];

    if ([self.currentPeripheral.peripheral isEqual:peripheral]) {
        [self.currentPeripheral didDisconnect];
    }
}

#pragma mark UARTPeripheralDelegate
- (void)didReadHardwareRevisionString:(NSString *)string
{
    NSLog(@"HW Revision: %@", string);
    if (self.connectionState != JogConnectionStateScanning) {
        return;
    }
    self.connectionState = JogConnectionStateConnected;
}

- (void)didReceiveData:(NSData *)newData
{
    int dataLength = (int)newData.length;
    uint8_t data[dataLength];

    [newData getBytes:&data length:dataLength];

    for (int i = 0; i<dataLength; i++) {

        if ((data[i] <= 0x1f) || (data[i] >= 0x80)) {    //null characters
            if ((data[i] != 0x9) && //0x9 == TAB
                (data[i] != 0xa) && //0xA == NL
                (data[i] != 0xd)) { //0xD == CR
                data[i] = 0xA9;
            }
        }
    }

    NSString *newString = [[NSString alloc]initWithBytes:&data
                                                  length:dataLength
                                                encoding:NSUTF8StringEncoding];
    NSLog(@"ReceivData: %@", newString);
    NSArray* stringComponents = [newString componentsSeparatedByString:@" "];

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
            }
        } else if ([command isEqualToString:@"POS"]) {
            // Not sure what to do about it saying exactly where it is.
            // We should probably do something about this, but for now
            // since we're not doing direct remote controlling we do everything by index.
            // Knowing the current position will allow us to estiamate animation times better.
        }
    }
}

- (void)uartDidEncounterError:(NSString *)error
{
    NSLog(@"ERROR: %@", error);
}

- (void)peripheralDidDisconnect
{
    NSLog(@"Peripheral disconnected");

    self.connectionState = JogConnectionStateNotConnected;
    // Original code disabled the connect button for 1 second.
}

@end
