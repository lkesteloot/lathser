//
//  LSBluetoothPeripheral.h
//  Lathser
//
//  Created by Kurt Schaefer on 5/9/15.
//  Copyright (c) 2015 Kurt Schaefer. All rights reserved.
//
//  This is a front end for bluetooth LE communications. It can scan for and connect to a
//  bluetooth peripheral. Using the UARTPeripheral directly sort of works, but I've had a
//  hard time with random silent failures.  Possibly associated with sending too much
//  info at one time and swamping the 9600 baud connection.
//
//  This communication requires that the Arduino confirm receipt of each string, and also allows a
//  for per line responses from the Arduino.  That seems to keep the sending buffer from
//  overflowing and lets us make specific requests of the Arduino with an easy async bock based interface.
//
//  Responses must be of the form *<response> or just * for a positive ack without response.
//  Data sent from the Arduino without the * prefix are assumed to not be associated with a sent string
//  and are instead sent to the didRecieveString method on the delegate.
//
//  This lib doesn't try to do anything fancy with retrying/checksum's etc.
//  The hope is that this is enough to mostly work without having to get too fancy, and if we do have
//  to improve it later the interface can remain the same.

#import <Foundation/Foundation.h>
#import "UARTPeripheral.h"


typedef NS_ENUM(NSInteger, LSPeripheralConnectionState) {
    LSPeripheralConnectionStateNotConnected = 0,
    LSPeripheralConnectionStateScanning,
    LSPeripheralConnectionStateConnected,
};


@protocol LSBluetoothPeripheralDelegate <NSObject>
- (void)didRecieveString:(NSString*)string;
- (void)connectionStateChanged:(LSPeripheralConnectionState)connectionState;
@end

@interface LSBluetoothPeripheral : NSObject
@property (nonatomic, assign) LSPeripheralConnectionState connectionState;
@property (nonatomic, weak) id<LSBluetoothPeripheralDelegate> delegate;

- (void)scanForPeripherals;
- (void)disconnect;

- (void)sendString:(NSString*)string
           success:(void (^)(NSString*response))success
           failure:(void (^)(NSString*error))failure
           finally:(void (^)())finally;

- (void)sendStringArray:(NSArray*)stringArray
                success:(void (^)(NSString*response))success
                failure:(void (^)(NSString*error))failure
                finally:(void (^)())finally;

@end
