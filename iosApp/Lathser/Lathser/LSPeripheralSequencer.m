//
//  LSPeripheralSequencer.m
//  Lathser
//
//  Created by Kurt Schaefer on 5/9/15.
//  Copyright (c) 2015 Kurt Schaefer. All rights reserved.
//


#import "LSPeripheralSequencer.h"

// This is just a data holding object that holds all the info associated with
// a given send request.
#pragma mark - LSSendInfo
@interface LSSendInfo : NSObject

@property (nonatomic, strong) NSArray* stringArray;
@property (nonatomic, assign) NSInteger acknowlagedStringCount;

@property (nonatomic, copy) void(^success)(NSString*);
@property (nonatomic, copy) void(^failure)(NSString*);
@property (nonatomic, copy) void(^finally)(void);
@end

@implementation LSSendInfo
@end



@interface LSPeripheralSequencer () <CBCentralManagerDelegate, UARTPeripheralDelegate>
@property (nonatomic, strong) CBCentralManager *cbManager;
@property (nonatomic, strong) UARTPeripheral* currentPeripheral;

@property (nonatomic, strong) NSMutableArray* sendInfoQueue;
@property (nonatomic, strong) NSTimer* sendTimeoutTimer;
@property (nonatomic, assign) NSInteger currentStringIndex;
@end

@implementation LSPeripheralSequencer

// We give the arduino a max of 2 seconds to respond.  Make this longer if your
// code doesn't poll the ble very often.
static CGFloat SEND_TIMEOUT = 2;
static const NSInteger SUSSPECTED_MAX_BUFFER_SIZE = 128;

- (instancetype)init
{
    self = [super init];
    if (self) {
        self.cbManager = [[CBCentralManager alloc] initWithDelegate:self queue:nil];
        self.connectionState = LSPeripheralConnectionStateNotConnected;
        self.sendInfoQueue = [[NSMutableArray alloc] init];
    }
    return self;
}


- (void)sendString:(NSString*)string
           success:(void (^)(NSString*responce))success
           failure:(void (^)(NSString*error))failure
           finally:(void (^)())finally
{
    [self sendStringArray:@[string] success:success failure:failure finally:finally];
}

- (void)sendStringArray:(NSArray*)stringArray
                success:(void (^)(NSString*responce))success
                failure:(void (^)(NSString*error))failure
                finally:(void (^)())finally
{
    LSSendInfo *sendInfo = [[LSSendInfo alloc]init];
    sendInfo.stringArray = stringArray;
    sendInfo.acknowlagedStringCount = 0;
    sendInfo.success = success;
    sendInfo.failure = failure;
    sendInfo.finally = finally;

    [self.sendInfoQueue addObject:sendInfo];
    [self startSending];
}

- (void)startSending
{
    // If this timer is active we are waiting for a response, so sending is already going on and we are done.
    if (self.sendTimeoutTimer || !self.sendInfoQueue.count) {
        return;
    }

    LSSendInfo *sendInfo = [self.sendInfoQueue firstObject];
    NSString *stringToSend = [sendInfo.stringArray objectAtIndex:sendInfo.acknowlagedStringCount];

    NSLog(@"writeString: %@", stringToSend);

    NSData *data = [NSData dataWithBytes:stringToSend.UTF8String length:stringToSend.length];
    if (data.length > SUSSPECTED_MAX_BUFFER_SIZE) {
        NSLog(@"Warning string \"%@\" may be too long to send", stringToSend);
    }
    [self.currentPeripheral writeRawData:data];

    self.sendTimeoutTimer = [NSTimer scheduledTimerWithTimeInterval:SEND_TIMEOUT target:self selector:@selector(sendTimedOut:) userInfo:sendInfo repeats:FALSE];
}

- (void)sendTimedOut:(NSTimer*)timer
{
    LSSendInfo *sendInfo = [timer userInfo];

    [self.sendTimeoutTimer invalidate];
    self.sendTimeoutTimer = nil;

    if (sendInfo.failure) {
        sendInfo.failure(@"Timed out");
    }
    if (sendInfo.finally) {
        sendInfo.finally();
    }

    if ([self.sendInfoQueue firstObject] == sendInfo) {
        [self.sendInfoQueue removeObjectAtIndex:0];
    }
}

- (void)setConnectionState:(LSPeripheralConnectionState)connectionState
{
    if (_connectionState == connectionState) {
        return;
    }
    _connectionState = connectionState;
    [self.delegate connectionStateChanged:connectionState];
}

- (void)scanForPeripherals
{
    // skip scanning if UART is already connected
    NSArray *connectedPeripherals = [self.cbManager retrieveConnectedPeripheralsWithServices:@[UARTPeripheral.uartServiceUUID]];
    if ([connectedPeripherals count] > 0) {
        [self connectPeripheral:[connectedPeripherals objectAtIndex:0]];
    } else {
        self.connectionState = LSPeripheralConnectionStateScanning;
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
    self.connectionState = LSPeripheralConnectionStateNotConnected;
    if (self.currentPeripheral.peripheral) {
        [self.cbManager cancelPeripheralConnection:self.currentPeripheral.peripheral];
    }
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
    if (self.connectionState != LSPeripheralConnectionStateScanning) {
        return;
    }
    self.connectionState = LSPeripheralConnectionStateConnected;
}

- (void)didReceiveData:(NSData *)newData
{
    int dataLength = (int)newData.length;
    uint8_t data[dataLength];

    [newData getBytes:&data length:dataLength];

    // I don't remember what this is for.  Seems dangerous.
    for (int i = 0; i<dataLength; i++) {

        if ((data[i] <= 0x1f) || (data[i] >= 0x80)) {    //null characters
            if ((data[i] != 0x9) && //0x9 == TAB
                (data[i] != 0xa) && //0xA == NL
                (data[i] != 0xd)) { //0xD == CR
                NSLog(@"STAMPING ON %d", i);
                data[i] = 0xA9;
            }
        }
    }

    NSString *receivedString = [[NSString alloc]initWithBytes:&data
                                                  length:dataLength
                                                encoding:NSUTF8StringEncoding];
    NSLog(@"ReceivData: %@", receivedString);
    // If it's an ack we mark the stuff as acknowlaged and advance the ack head.
    if (receivedString.length > 0 && [receivedString characterAtIndex:0] == '*') {
        [self.sendTimeoutTimer invalidate];
        self.sendTimeoutTimer = nil;
        LSSendInfo *sendInfo = [self.sendInfoQueue firstObject];
        sendInfo.acknowlagedStringCount++;

        // If we've sent all the strings in the array we pop off the sendInfo and
        // inform the caller.
        if (sendInfo.acknowlagedStringCount >= sendInfo.stringArray.count) {
            [self.sendInfoQueue removeObjectAtIndex:0];

            if (sendInfo.success) {
                sendInfo.success([receivedString substringFromIndex:1]);
            }
            if (sendInfo.finally) {
                sendInfo.finally();
            }
        }
        // If there are any strings left to send this will send them and schedule
        // a new timeout, etc.
        [self startSending];
    } else {
        [self.delegate didRecieveString:receivedString];
    }
}

- (void)uartDidEncounterError:(NSString *)error
{
    NSLog(@"ERROR: %@", error);
}

- (void)peripheralDidDisconnect
{
    NSLog(@"Peripheral disconnected");
    self.connectionState = LSPeripheralConnectionStateNotConnected;
    // Original code disabled the connect button for 1 second.
}


@end
