//
//  FirstViewController.m
//  BlueToothLETest
//
//  Created by Kurt Schaefer on 4/13/14.
//  Copyright (c) 2014 Kurt Schaefer. All rights reserved.
//

#import "UARTPeripheral.h"
#import "JogViewController.h"
#import "DialView.h"

typedef NS_ENUM(NSInteger, JogConnectionState) {
    JogConnectionStateNotConnected = 0,
    JogConnectionStateScanning,
    JogConnectionStateConnected,
};


@interface JogViewController ()
@property (nonatomic, strong) CBCentralManager *cbManager;

@property (weak, nonatomic) IBOutlet UIButton *connectionButton;
@property (weak, nonatomic) IBOutlet UILabel *connectionStatusLabel;

@property (nonatomic, strong) UARTPeripheral* currentPeripheral;
@property (nonatomic, assign) JogConnectionState connectionState;


@property (nonatomic, strong) IBOutlet DialView* dialView;
@property (nonatomic, strong) IBOutlet UIView* thermalSensorView;
@property (nonatomic, strong) IBOutlet UIImageView* thermalSensorImageView;

@property (weak, nonatomic) IBOutlet UIImageView *nearLimitIndicatorImageView;
@property (weak, nonatomic) IBOutlet UIImageView *farLimitIndicatorImageView;
@property (nonatomic, assign) BOOL nearLimitReached;
@property (nonatomic, assign) BOOL farLimitReached;

@property (nonatomic, strong) NSMutableArray* positions;

@end

@implementation JogViewController


- (id)initWithCoder:(NSCoder *)aDecoder
{
    self = [super initWithCoder:aDecoder];
    if (self) {
        self.cbManager = [[CBCentralManager alloc] initWithDelegate:self queue:nil];
        self.connectionState = JogConnectionStateNotConnected;

        self.positions = [[NSMutableArray alloc] init];
        [self.positions addObject:@(0.0f)];
        [self.positions addObject:@(1*M_PI/8.0)];
        [self.positions addObject:@(2*M_PI/8.0)];
        [self.positions addObject:@(3*M_PI/8.0)];
        [self.positions addObject:@(4*M_PI/8.0)];
        [self.positions addObject:@(5*M_PI/8.0)];
        [self.positions addObject:@(6*M_PI/8.0)];
        [self.positions addObject:@(6*M_PI/8.0 + 9*M_PI/8.0)];

        [self updateThermalSensorColor:85];
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

- (IBAction)sendSequenceButtonTouchUpinside:(id)sender
{
    // 7 1/16 steps plus a 9/16 step at the end.
    [self sendString:@"q"];
    [self sendString:@"a0 "];
    [self sendString:@"a800 "];
    [self sendString:@"a1600 "];
    [self sendString:@"a2400 "];
    [self sendString:@"a3200 "];
    [self sendString:@"a4000 "];
    [self sendString:@"a4800 "];
    [self sendString:@"a5600 "];
    [self sendString:@"a12800 "];
    [self sendString:@"s"];
}

- (IBAction)previousButtonTouchUpInside:(id)sender
{
    if (self.dialView.currentPositionIndex > 0) {
        self.dialView.currentPositionIndex--;
    }
    [self sendString:@"p"];
}

- (IBAction)nextButtonTouchUpInside:(id)sender
{
    if (self.dialView.currentPositionIndex + 1 < self.positions.count) {
        self.dialView.currentPositionIndex++;
    }
    [self sendString:@"n"];
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

- (void)updateThermalSensorColor:(NSInteger)value
{
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
    self.thermalSensorView.backgroundColor = color;
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
}

- (void)updateLimitIndicator:(UIImageView*)indicatorImageView withIsReached:(BOOL)isReached
{
    if (isReached) {
        [indicatorImageView setImage:[UIImage imageNamed:@"redIndicatorCircle32x32"]];
    } else {
        [indicatorImageView setImage:[UIImage imageNamed:@"whiteIndicatorCircle32x32"]];
    }
}

- (void)setNearLimitReached:(BOOL)nearLimitReached
{
    if (_nearLimitReached == nearLimitReached) {
 //       return;
    }
    _nearLimitReached = nearLimitReached;
    [self updateLimitIndicator:self.nearLimitIndicatorImageView withIsReached:nearLimitReached];
}

- (void)setFarLimitReached:(BOOL)farLimitReached
{
    if (_farLimitReached == farLimitReached) {
        return;
    }
    _farLimitReached = farLimitReached;
    [self updateLimitIndicator:self.farLimitIndicatorImageView withIsReached:farLimitReached];
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
            // TODO: Indicate thermal pulse, hopefully by drawing an expanding ring
            // out of the thermal sensor display.
        }
    } else if (stringComponents.count == 2) {
        NSString* command = [stringComponents objectAtIndex:0];
        NSString* arg = [stringComponents objectAtIndex:1];
        if ([command isEqualToString:@"TEMP"]) {
            [self updateThermalSensorColor:[arg integerValue]];
        } else if ([command isEqualToString:@"RUN"]) {
            self.dialView.currentPositionIndex = [arg integerValue];
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
